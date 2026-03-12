"""
Report Parser — legge e parsa report Power BI in formato PBIR e PBIR-Legacy
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .report_models import (
    Report,
    ReportPage,
    Visual,
    Bookmark,
    ReportExtensions,
    ReportFormat,
    VisualType,
)

logger = logging.getLogger(__name__)


class ReportParser:
    """
    Parser per report Power BI in formato PBIR e PBIR-Legacy.
    
    Supporta:
    - Rilevamento automatico del formato
    - Parsing di pagine, visual, bookmarks, report extensions
    - Gestione errori con graceful degradation
    """
    
    def parse(self, report_path: Path) -> Report:
        """
        Parse una cartella .Report e restituisce un oggetto Report.
        
        Args:
            report_path: Path alla cartella .Report o .Report/definition
            
        Returns:
            Report object con struttura completa
            
        Raises:
            FileNotFoundError: Se la cartella non esiste
            ValueError: Se il formato non è riconosciuto
        """
        if not report_path.exists():
            raise FileNotFoundError(
                f"Report path not found: {report_path}\n"
                f"Expected a .Report folder or .Report/definition folder"
            )
        
        try:
            definition_path = self._find_definition_dir(report_path)
            format_type = self._detect_format(definition_path)
            
            logger.info(f"Detected format: {format_type.value}")
            
            if format_type == ReportFormat.PBIR:
                return self._parse_pbir(definition_path)
            else:
                return self._parse_pbir_legacy(definition_path)
                
        except Exception as e:
            logger.error(f"Complete parsing failure for {report_path}: {e}")
            # Graceful degradation: restituisci report vuoto con errore
            report = Report(
                name=report_path.name,
                format=ReportFormat.PBIR,
                pages=[],
                bookmarks=[],
            )
            return report
    
    def _find_definition_dir(self, root: Path) -> Path:
        """
        Trova la cartella definition/ nella struttura .Report.
        
        Accetta:
        - Una cartella che è la root .Report → root/definition/
        - Una cartella che contiene .Report → root/*.Report/definition/
        - La cartella definition/ stessa
        """
        # Già la cartella definition?
        if (root / "report.json").exists() or (root / "pages").exists():
            return root
        
        # Standard layout: root/definition/
        candidate = root / "definition"
        if candidate.exists():
            return candidate
        
        # Forse root contiene una *.Report child
        for child in root.iterdir():
            if child.is_dir() and ".Report" in child.name:
                defn = child / "definition"
                if defn.exists():
                    return defn
        
        raise FileNotFoundError(
            f"Cannot locate a report definition folder under: {root}\n"
            "Expected one of:\n"
            "  <root>/definition/\n"
            "  <root>/<name>.Report/definition/"
        )
    
    def _detect_format(self, definition_path: Path) -> ReportFormat:
        """
        Rileva automaticamente PBIR vs PBIR-Legacy.
        
        PBIR format: presenza di cartelle pages/, bookmarks/
        PBIR-Legacy: presenza di report.json come file (non cartella)
        """
        if (definition_path / "pages").is_dir():
            return ReportFormat.PBIR
        elif (definition_path / "report.json").is_file():
            return ReportFormat.PBIR_LEGACY
        else:
            raise ValueError(
                f"Cannot recognize report format in: {definition_path}\n"
                f"Expected either:\n"
                f"  - PBIR format: pages/ and bookmarks/ folders\n"
                f"  - PBIR-Legacy format: report.json file"
            )
    
    def _safe_json_load(self, file_path: Path) -> dict:
        """
        Carica JSON con error handling robusto.
        
        Args:
            file_path: Path al file JSON
            
        Returns:
            Dizionario parsato, o {} se errore
        """
        try:
            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(
                f"Malformed JSON in {file_path.name} at line {e.lineno}, col {e.colno}: {e.msg}"
            )
            return {}
        except Exception as e:
            logger.error(f"Cannot read {file_path.name}: {e}")
            return {}
    
    def _parse_pbir(self, definition_path: Path) -> Report:
        """Parse formato PBIR (struttura a cartelle)"""
        # Il nome viene dalla cartella .Report (parent di definition/)
        report_name = definition_path.parent.name
        if report_name.endswith(".Report"):
            report_name = report_name[: -len(".Report")]
        
        report = Report(
            name=report_name,
            format=ReportFormat.PBIR,
        )
        
        # Parse pages
        pages_dir = definition_path / "pages"
        if pages_dir.exists():
            report.pages = self._parse_pages(pages_dir)
        
        # Parse bookmarks
        bookmarks_dir = definition_path / "bookmarks"
        if bookmarks_dir.exists():
            report.bookmarks = self._parse_bookmarks(bookmarks_dir)
        
        # Parse report extensions
        extensions_file = definition_path / "reportExtensions.json"
        if extensions_file.exists():
            report.extensions = self._parse_report_extensions(extensions_file)
        
        # Parse version
        version_file = definition_path / "version.json"
        if version_file.exists():
            version_data = self._safe_json_load(version_file)
            report.version = version_data.get("version", "")
        
        return report
    
    def _parse_pages(self, pages_dir: Path) -> list[ReportPage]:
        """Parse cartella pages/ in formato PBIR"""
        pages = []
        
        for page_dir in sorted(pages_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            
            try:
                page = self._parse_page(page_dir)
                pages.append(page)
            except Exception as e:
                logger.warning(f"Failed to parse page {page_dir.name}: {e}")
                continue
        
        return pages
    
    def _parse_page(self, page_dir: Path) -> ReportPage:
        """Parse singola pagina da page.json"""
        page_json_path = page_dir / "page.json"
        page_json = self._safe_json_load(page_json_path)
        
        # Campo obbligatorio con fallback
        name = page_json.get("name")
        if not name:
            logger.warning(f"Missing 'name' field in {page_dir}/page.json, using folder name")
            name = page_dir.name
        
        # Campi opzionali con default
        display_name = page_json.get("displayName", name)
        is_hidden = page_json.get("isHidden", False)
        width = page_json.get("width", 0)
        height = page_json.get("height", 0)
        filters = page_json.get("filters", [])
        
        # Check drillthrough
        config = page_json.get("config", {})
        has_drillthrough = "drillthrough" in config or "drillThrough" in config
        
        # Parse visuals
        visuals_dir = page_dir / "visuals"
        visuals = []
        if visuals_dir.exists():
            visuals = self._parse_visuals(visuals_dir)
        
        return ReportPage(
            name=name,
            display_name=display_name,
            visuals=visuals,
            is_hidden=is_hidden,
            has_drillthrough=has_drillthrough,
            filters=filters if isinstance(filters, list) else [],
            width=width,
            height=height,
        )
    
    def _parse_visuals(self, visuals_dir: Path) -> list[Visual]:
        """Parse cartella visuals/ di una pagina"""
        visuals = []
        
        for visual_dir in sorted(visuals_dir.iterdir()):
            if not visual_dir.is_dir():
                continue
            
            try:
                visual = self._parse_visual(visual_dir)
                visuals.append(visual)
            except Exception as e:
                logger.warning(f"Failed to parse visual {visual_dir.name}: {e}")
                continue
        
        return visuals
    
    def _parse_visual(self, visual_dir: Path) -> Visual:
        """Parse singolo visual da visual.json"""
        visual_json_path = visual_dir / "visual.json"
        visual_json = self._safe_json_load(visual_json_path)
        
        name = visual_json.get("name", visual_dir.name)
        config = visual_json.get("config", {})

        # New PBIR format: visualType lives in visual.visualType (not config.singleVisual)
        visual_data = visual_json.get("visual", {})

        # Estrai tipo visual — prova prima il nuovo formato, poi il vecchio
        visual_type = Visual.extract_type(visual_data) if visual_data else VisualType.UNKNOWN
        if visual_type == VisualType.UNKNOWN:
            visual_type = Visual.extract_type(config)

        # Custom visual: qualsiasi tipo non mappato nell'enum è custom
        custom_visual_name = None
        if visual_type == VisualType.UNKNOWN:
            visual_type_str = (
                visual_data.get("visualType", "")
                or config.get("singleVisual", {}).get("visualType", "")
                or config.get("visualType", "")
            )
            if visual_type_str:
                visual_type = VisualType.CUSTOM
                custom_visual_name = visual_type_str
        
        # Check mobile layout
        mobile_json_path = visual_dir / "mobile.json"
        has_mobile_layout = mobile_json_path.exists()
        
        return Visual(
            name=name,
            visual_type=visual_type,
            custom_visual_name=custom_visual_name,
            has_mobile_layout=has_mobile_layout,
            config=config,
        )
    
    def _parse_bookmarks(self, bookmarks_dir: Path) -> list[Bookmark]:
        """Parse cartella bookmarks/"""
        bookmarks = []
        
        for bookmark_file in sorted(bookmarks_dir.glob("*.bookmark.json")):
            try:
                bookmark_json = self._safe_json_load(bookmark_file)
                
                name = bookmark_json.get("name", bookmark_file.stem)
                display_name = bookmark_json.get("displayName", name)
                page_name = bookmark_json.get("explorationState", {}).get("activeSection")
                
                bookmarks.append(Bookmark(
                    name=name,
                    display_name=display_name,
                    page_name=page_name,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse bookmark {bookmark_file.name}: {e}")
                continue
        
        return bookmarks
    
    def _parse_report_extensions(self, extensions_file: Path) -> ReportExtensions:
        """Parse reportExtensions.json"""
        extensions_json = self._safe_json_load(extensions_file)
        
        measures = []
        entities = extensions_json.get("entities", [])
        
        for entity in entities:
            if isinstance(entity, dict):
                measure_name = entity.get("name")
                if measure_name:
                    measures.append(measure_name)
        
        return ReportExtensions(
            measures=measures,
            has_extensions=len(measures) > 0,
        )
    
    def _parse_pbir_legacy(self, definition_path: Path) -> Report:
        """Parse formato PBIR-Legacy (singolo file)"""
        report_json_path = definition_path / "report.json"
        report_json = self._safe_json_load(report_json_path)
        
        # Il nome viene dalla cartella .Report (parent di definition/)
        folder_name = definition_path.parent.name
        if folder_name.endswith(".Report"):
            folder_name = folder_name[: -len(".Report")]
        report_name = folder_name
        
        report = Report(
            name=report_name,
            format=ReportFormat.PBIR_LEGACY,
        )
        
        # Parse pages from legacy format
        pages_data = report_json.get("pages", [])
        for page_data in pages_data:
            try:
                page = self._parse_page_legacy(page_data)
                report.pages.append(page)
            except Exception as e:
                logger.warning(f"Failed to parse legacy page: {e}")
                continue
        
        # Parse bookmarks from legacy format
        bookmarks_data = report_json.get("bookmarks", [])
        for bookmark_data in bookmarks_data:
            try:
                name = bookmark_data.get("name", "")
                display_name = bookmark_data.get("displayName", name)
                report.bookmarks.append(Bookmark(
                    name=name,
                    display_name=display_name,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse legacy bookmark: {e}")
                continue
        
        return report
    
    def _parse_page_legacy(self, page_data: dict) -> ReportPage:
        """Parse singola pagina da formato legacy"""
        name = page_data.get("name", "")
        display_name = page_data.get("displayName", name)
        is_hidden = page_data.get("isHidden", False)
        width = page_data.get("width", 0)
        height = page_data.get("height", 0)
        filters = page_data.get("filters", [])
        
        # Parse visual containers
        visuals = []
        visual_containers = page_data.get("visualContainers", [])
        for container in visual_containers:
            try:
                config = container.get("config", {})
                visual_name = container.get("name", "")
                visual_type = Visual.extract_type(config)
                
                visuals.append(Visual(
                    name=visual_name,
                    visual_type=visual_type,
                    config=config,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse legacy visual: {e}")
                continue
        
        return ReportPage(
            name=name,
            display_name=display_name,
            visuals=visuals,
            is_hidden=is_hidden,
            filters=filters if isinstance(filters, list) else [],
            width=width,
            height=height,
        )

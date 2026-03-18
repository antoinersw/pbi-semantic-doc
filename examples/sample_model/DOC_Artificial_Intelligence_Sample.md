# DOC — Artificial Intelligence Sample

> Combined Power BI project documentation &middot; Generated 2026-03-18

---

## Contents

- [Semantic Model](#semantic-model) — 9 tables, 21 measures, 12 relationships
- [Report](#report) — 3 pages, 235 visuals


---

## Semantic Model

## Contents

- [Overview](#overview)
- [Data Sources](#data-sources) — 1 connector
- [Relationships](#relationships) — 12 relationships
- [Row Level Security](#row-level-security) — 2 roles
- **Tables**
  - [Accounts](#table-accounts) — 📥 Import · 18 cols
  - [Campaigns](#table-campaigns) — 📥 Import · 3 cols
  - [Case Calendar](#table-case-calendar) — 🧮 Calculated · 14 cols
  - [Cases](#table-cases) — 📥 Import · 19 cols · 10 measures
  - [Contacts](#table-contacts) — 📥 Import · 13 cols
  - [Opportunities](#table-opportunities) — 📥 Import · 19 cols · 10 measures
  - [Opportunity Calendar](#table-opportunity-calendar) — 🧮 Calculated · 9 cols
  - [Owners](#table-owners) — 📥 Import · 2 cols · 1 measure
  - [Products](#table-products) — 📥 Import · 4 cols
- [Measures Index](#measures-index-az) — 22 measures
- [Unused Columns](#unused-columns) — 95 columns
- [Hidden Objects](#hidden-objects) — 3 tables, 29 columns

## Overview

| | |
|---|---|
| Tables | 9 visible, 3 hidden |
| Columns | 101 visible, 29 hidden |
| Measures | 22 |
| Relationships | 12 (2 inactive) |
| RLS Roles | 2 |
| **Complexity Index** | **🟢 24%** |

## Data Sources

| Table | Connector | Server / Path | Database | Mode | Steps | Query Folding |
|-------|-----------|--------------|----------|------|-------|---------------|
| `Accounts` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 3 | — N/A |
| `Campaigns` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 4 | — N/A |
| `Case Calendar` | — | — | — | Calculated (DAX) | — | — |
| `Cases` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 6 | — N/A |
| `Contacts` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 3 | — N/A |
| `Industries` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 4 | — N/A |
| `Opportunities` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 5 | — N/A |
| `Opportunity Calendar` | — | — | — | Calculated (DAX) | — | — |
| `Opportunity Forecast Adjustment` | — | — | — | Calculated (DAX) | — | — |
| `Owners` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 6 | — N/A |
| `Products` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 5 | — N/A |
| `Territories` | Excel | C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx *(param)* | <File.Contents()> | Import | 3 | — N/A |

## Relationships

<details>
<summary>🔗 12 relationships — click to expand</summary>

| From | | To | Cardinality | Cross-filter | Active |
|---|---|---|---|---|---|
| `Accounts`['Account Owner] | → | `Owners`['Sales owner] | many-to-one | single | ✅ |
| `Opportunities`[AccountSeq] | → | `Accounts`[AccountSeq] | many-to-one | single | ✅ |
| `Cases`[AccountSeq] | → | `Accounts`[AccountSeq] | many-to-one | single | ✅ |
| `Contacts`[AccountSeq] | → | `Accounts`[AccountSeq] | many-to-one | single | ✅ |
| `Accounts`[IndustrySeq] | → | `Industries`[IndustrySeq] | many-to-one | single | ✅ |
| `Opportunities`[ProductSeq] | → | `Products`[ProductSeq] | many-to-one | single | ✅ |
| `Cases`[ProductSeq] | → | `Products`[ProductSeq] | many-to-one | single | ✅ |
| `Opportunities`[SystemUserSeq] | → | `Owners`[SystemUserSeq] | many-to-one | single | ⬜ |
| `Cases`[SystemUserSeq] | → | `Owners`[SystemUserSeq] | many-to-one | single | ⬜ |
| `Opportunities`[CloseDate] | → | `Opportunity Calendar'`[DAY] | many-to-one | single | ✅ |
| `Opportunities`[CampaignSeq] | → | `Campaigns`[CampaignSeq] | many-to-one | single | ✅ |
| `Cases`['Case Created On] | → | `Case Calendar'`[Date] | many-to-one | single | ✅ |

</details>

## Row Level Security

| Role | Permission | Table | Filter |
|------|-----------|-------|--------|
| **admin_role** | read | `Owners` | `[Manager] == "Weiler, Anne"` |
| **user_role** | read | `Owners` | `[Manager] == "Low, Spencer" && [Manager] == "Weiler, Anne"` |

## Table: `Accounts`

<details>
<summary>📥 Import · 18 cols · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (18 visible, 3 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Account Name` | string |  |  | |
| `Street` | string |  |  | |
| `City` | string |  |  | |
| `State or Province` | string |  |  | |
| `Postal Code` | string |  |  | |
| `Country` | string |  |  | |
| `Latitude` | double |  |  | |
| `Longitude` | double |  |  | |
| `Phone` | string |  |  | |
| `Annual Revenue` | int64 |  | `0` | |
| `Number of Employees` | int64 |  | `0` | |
| `AccountID` | string |  |  | |
| `Industry Lookup` | unknown |  |  | |
| `Territory` | string |  |  | |
| `Region` | string |  |  | |
| `AccountOwnerSeq` | int64 |  | `0` | |
| `Industry` | string |  |  | |
| `Account Number` | string |  |  | |
| `Account Owner` | string |  |  | ✗ |
| `AccountSeq` | int64 |  | `0` | ✗ |
| `IndustrySeq` | int64 |  | `0` | ✗ |

</details>

<details>
<summary>🔌 Power Query — 3 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `AccountTbl_Table` | navigation | ✅ |
| 3 | `#"Changed Type"` | type_cast | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
AccountTbl_Table = Source{[Item="AccountTbl",Kind="Table"]}[Data],
#"Changed Type" = Table.TransformColumnTypes(AccountTbl_Table,{{"AccountSeq", Int64.Type}, {"AccountID", type text}, {"Account Name", type text}, {"Street", type text}, {"City", type text}, {"State or Province", type any}, {"Postal Code", type text}, {"Country", type text}, {"Latitude", type number}, {"Longitude", type number}, {"Territory", type text}, {"Region", type text}, {"Phone", type text}, {"Number of Employees", Int64.Type}, {"Annual Revenue", Int64.Type}, {"IndustrySeq", Int64.Type}, {"Industry", type text}, {"AccountOwnerSeq", Int64.Type}, {"Account Owner", type text}})
in
#"Changed Type"
```

</details>

</details>

## Table: `Campaigns`

<details>
<summary>📥 Import · 3 cols · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (3 visible, 1 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Type` | string |  |  | |
| `Campaign Name` | string |  |  | |
| `Factor` | int64 |  | `0` | |
| `CampaignSeq` | int64 |  | `0` | ✗ |

</details>

<details>
<summary>🔌 Power Query — 4 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `CampaignsTbl_Table` | navigation | ✅ |
| 3 | `#"Changed Type"` | type_cast | ✅ |
| 4 | `#"Renamed Columns"` | rename | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
CampaignsTbl_Table = Source{[Item="CampaignsTbl",Kind="Table"]}[Data],
#"Changed Type" = Table.TransformColumnTypes(CampaignsTbl_Table,{{"CampaignSeq", Int64.Type}, {"Type", type text}, {"Name", type text}, {"Factor", Int64.Type}}),
#"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"Name", "Campaign Name"}})
in
#"Renamed Columns"
```

</details>

</details>

## Table: `Case Calendar`

<details>
<summary>🧮 Calculated (DAX) · 14 cols — click to expand</summary>

> 🧮 **Calculated table** (DAX)

<details>
<summary>### Columns (14 visible, 3 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Date` | unknown |  | `Short Date` | |
| `DAY` | unknown |  |  | |
| `DaySeq` | unknown |  | `0` | |
| `YEAR` | unknown |  | `0` | |
| `MONTH` | unknown |  |  | |
| `YEAR MONTH` | unknown |  |  | |
| `YEAR WEEK` | unknown |  |  | |
| `WEEK` | unknown |  | `General Date` | |
| `RELATIVE WEEK` | unknown |  |  | |
| `RELATIVE DAY` | int64 |  | `0` | |
| `RELATIVE 07 DAY PERIOD` | unknown |  |  | |
| `RELATIVE 30 DAY PERIOD` | unknown |  |  | |
| `RELATIVE MONTH` | unknown |  | `0` | |
| `Weekday` | unknown |  |  | |
| `MONTH NUMBER` | unknown |  | `0` | ✗ |
| `YEAR MONTH NUMBER` | unknown |  | `0` | ✗ |
| `WeekdaySeq` | unknown |  | `0` | ✗ |

</details>

</details>

## Table: `Cases`

<details>
<summary>📥 Import · 19 cols · 10 measures · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (19 visible, 4 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Status` | string |  |  | |
| `Agent` | string |  |  | |
| `Title` | string |  |  | |
| `Origin` | string |  |  | |
| `Is Escalated` | boolean |  |  | |
| `Subject` | string |  |  | |
| `CSAT Label` | string |  |  | |
| `Resolution Minutes` | int64 |  | `#,0.0` | |
| `Severity` | string |  |  | |
| `Is SLA Violation` | boolean |  |  | |
| `CSAT` | int64 |  | `0` | |
| `SLA Compliance Goal` | unknown |  | `0%;-0%;0%` | |
| `Resolution Minutes Goal` | unknown |  | `0` | |
| `CSAT Goal` | unknown |  | `0.00` | |
| `Escalations Goal` | unknown |  | `0%;-0%;0%` | |
| `Minutes to First Contact` | int64 |  |  | |
| `Activities` | int64 |  | `0` | |
| `Topic` | unknown |  |  | |
| `CaseSeq` | int64 |  | `0` | |
| `Case Created On` | dateTime |  |  | ✗ |
| `SystemUserSeq` | int64 |  | `0` | ✗ |
| `AccountSeq` | int64 |  | `0` | ✗ |
| `ProductSeq` | int64 |  | `0` | ✗ |

</details>

### Measures

#### `Case Count`

**Format:** `#,0`

```dax
COUNTROWS('Cases')
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Cases % by Product`

*Uses CALCULATE · Removes filters · Safe division*

**Format:** `0.00%;-0.00%;0.00%`

```dax
DIVIDE(
[Case Count],
CALCULATE(
[Case Count],All('Products')
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔗 **Depends on:** `[Case Count]`

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Products`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Cases % by Subject`

*Uses CALCULATE · Removes filters · Safe division*

**Format:** `0.0%;-0.0%;0.0%`

```dax
DIVIDE(
[Case Count],
CALCULATE(
[Case Count],All('Cases'[Subject])
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Subject`]

🔗 **Depends on:** `[Case Count]`

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Cases MoM%`

*Time intelligence · Uses CALCULATE · Uses variables · Safe division*

**Format:** `0.0%;-0.0%;0.0%`

```dax
VAR __PREV_MONTH = CALCULATE([Case Count], DATEADD('Case Calendar'[Date], -1, MONTH))
RETURN
DIVIDE([Case Count] - __PREV_MONTH, __PREV_MONTH)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Case Calendar`[`Date`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

🏷️ **Flags:** ⏱️ Time intelligence

</details>
#### `CSAT Impact`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Topic] <> SELECTEDVALUE ( 'Cases'[Topic] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`Topic`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `CSAT Impact - Agent`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Agent] <> SELECTEDVALUE ( 'Cases'[Agent] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Agent`], `Cases`[`CSAT`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `CSAT Impact - Products`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[ProductSeq] <> SELECTEDVALUE ( 'Cases'[ProductSeq] )  )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`ProductSeq`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `CSAT Impact - Subject`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Subject] <> SELECTEDVALUE ( 'Cases'[Subject] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`Subject`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Escalations`

*Uses CALCULATE · Safe division*

**Format:** `#,0%;-#,0%;#,0%`

```dax
DIVIDE(CALCULATE(COUNTROWS('Cases'),'Cases'[Is Escalated] = TRUE()) , [Case Count],0)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Is Escalated`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `SLA Compliance`

*Uses CALCULATE · Safe division*

**Format:** `#,0%;-#,0%;#,0%`

```dax
DIVIDE(CALCULATE(COUNTROWS('Cases'),'Cases'[Is SLA Violation] = FALSE()) , [Case Count],0)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Is SLA Violation`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

<details>
<summary>🔌 Power Query — 6 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `IncidentTbl_Table` | navigation | ✅ |
| 3 | `#"Removed Other Columns"` | select_columns | ✅ |
| 4 | `#"Inserted Text Before Delimiter"` | add_column | ❓ |
| 5 | `#"Changed Type"` | type_cast | ✅ |
| 6 | `#"Renamed Columns"` | rename | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
IncidentTbl_Table = Source{[Item="IncidentTbl",Kind="Table"]}[Data],
#"Removed Other Columns" = Table.SelectColumns(IncidentTbl_Table,{"IncidentSeq", "CreatedOn", "Resolution Minutes", "Minutes to First Contact", "Activities", "Status", "SystemUserSeq", "Owner", "AccountSeq", "ProductSeq", "Title", "Origin", "Severity", "Is Escalated", "Is SLA Violation", "Subject", "CustomerSatScore"}),
#"Inserted Text Before Delimiter" = Table.AddColumn(#"Removed Other Columns", "CSAT", each Text.BeforeDelimiter([CustomerSatScore], "-"), type text),
#"Changed Type" = Table.TransformColumnTypes(#"Inserted Text Before Delimiter",{{"CreatedOn", type date}, {"Resolution Minutes", Int64.Type}, {"Status", type text}, {"Owner", type text}, {"Title", type text}, {"Origin", type text}, {"Severity", type text}, {"Is Escalated", type logical}, {"Is SLA Violation", type logical}, {"Subject", type text}, {"CustomerSatScore", type text}, {"CSAT", Int64.Type}, {"Minutes to First Contact", Int64.Type}, {"Activities", Int64.Type}, {"IncidentSeq", Int64.Type}, {"SystemUserSeq", Int64.Type}, {"AccountSeq", Int64.Type}, {"ProductSeq", Int64.Type}}),
#"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"IncidentSeq", "CaseSeq"}, {"CustomerSatScore", "CSAT Label"}, {"CreatedOn", "Case Created On"}, {"Owner", "Agent"}})
in
#"Renamed Columns"
```

</details>

</details>

## Table: `Contacts`

<details>
<summary>📥 Import · 13 cols · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (13 visible, 2 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Contact` | string |  |  | |
| `Job Title` | string |  |  | |
| `Street` | string |  |  | |
| `City` | string |  |  | |
| `State or Province` | string |  |  | |
| `Postal Code` | string |  |  | |
| `Country` | string |  |  | |
| `Latitude` | double |  |  | |
| `Longitude` | double |  |  | |
| `Phone` | string |  |  | |
| `ContactSeq` | int64 |  | `0` | |
| `FirstName` | string |  |  | |
| `LastName` | string |  |  | |
| `ContactID` | string |  |  | ✗ |
| `AccountSeq` | int64 |  | `0` | ✗ |

</details>

<details>
<summary>🔌 Power Query — 3 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `ContactTbl_Table` | navigation | ✅ |
| 3 | `#"Changed Type"` | type_cast | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
ContactTbl_Table = Source{[Item="ContactTbl",Kind="Table"]}[Data],
#"Changed Type" = Table.TransformColumnTypes(ContactTbl_Table,{{"ContactID", type text}, {"Contact", type text}, {"Job Title", type text}, {"Street", type text}, {"City", type text}, {"State or Province", type text}, {"Postal Code", type text}, {"Country", type text}, {"Latitude", type number}, {"Longitude", type number}, {"Phone", type text}, {"ContactSeq", Int64.Type}, {"AccountSeq", Int64.Type}})
in
#"Changed Type"
```

</details>

</details>

## Table: `Opportunities`

<details>
<summary>📥 Import · 19 cols · 10 measures · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (19 visible, 6 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Budget` | int64 |  | `\$#,0.###############;(\$#,0.###############);\$#,0.###############` | |
| `Topic` | string |  |  | |
| `Purchase Process` | string |  |  | |
| `Decision Maker Identified` | boolean |  |  | |
| `Status` | string |  |  | |
| `PipelineStep` | string |  |  | |
| `Value` | int64 |  | `\$#,0;(\$#,0);\$#,0` | |
| `Weeks Open` | unknown |  | `0` | |
| `DaysToClose` | int64 |  | `0` | |
| `Discount` | double |  | `0.0%;-0.0%;0.0%` | |
| `Probability` | double |  | `0.0%;-0.0%;0.0%` | |
| `Rating` | string |  |  | |
| `Days Remaining In Pipeline` | unknown |  | `0` | |
| `Probability (raw)` | double |  | `0.0%;-0.0%;0.0%` | |
| `Opportunity Owner Name` | string |  |  | |
| `OpportunitySeq` | int64 |  | `0` | |
| `Product Name` | string |  |  | |
| `Campaign Name` | string |  |  | |
| `Blank` | unknown |  | `0` | |
| `CloseDate` | dateTime |  | `Short Date` | ✗ |
| `Opportunity Created On` | dateTime |  | `Long Date` | ✗ |
| `AccountSeq` | int64 |  | `0` | ✗ |
| `ProductSeq` | int64 |  | `0` | ✗ |
| `SystemUserSeq` | string |  |  | ✗ |
| `CampaignSeq` | string |  |  | ✗ |

</details>

### Measures

#### `Close %`

*Division (check for zero)*

**Format:** `0.0%;-0.0%;0.0%`

```dax
[Count of Won]/([Count of Won]+[Count of Lost])
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

🔗 **Depends on:** `[Count of Won]`, `[Count of Lost]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Count of Lost`

*Preserves filters · Row filter*

**Format:** `#,0`

```dax
COUNTAX(
FILTER(
KEEPFILTERS(Opportunities),Opportunities[Status] = "Lost"
),
Opportunities[OpportunitySeq]
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Count of Won`

*Preserves filters · Row filter*

**Format:** `#,0`

```dax
COUNTAX(
FILTER(
KEEPFILTERS(Opportunities),Opportunities[Status] = "Won"
),
Opportunities[OpportunitySeq]
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Forecast`

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
([Revenue Won]+[Revenue In Pipeline])
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

🔗 **Depends on:** `[Revenue Won]`, `[Revenue In Pipeline]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Forecast %`

*Division (check for zero)*

**Format:** `#,0%;-#,0%;#,0%`

```dax
(([Revenue Won]+[Revenue In Pipeline]))/ [Rev Goal]
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

🔗 **Depends on:** `[Revenue Won]`, `[Revenue In Pipeline]`, `[Rev Goal]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Opportunity Count`

**Format:** `#,0`

```dax
COUNTAX(Opportunities,TRUE())
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Opportunity Count In Pipeline`

*Aggregation: COUNT*

**Format:** `#,0`

```dax
CALCULATE (
COUNT( Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
--  && Opportunities[PipelineStep] IN { "3-Pipeline", "4-Mandate", "5-Close" }
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Revenue In Pipeline`

*Uses variables · Division (check for zero)*

**Format:** `\$#,0.0;(\$#,0.0);\$#,0.0`

```dax
VAR Revenue =
CALCULATE (
SUMX ( Opportunities, Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
&& VALUE(LEFT(Opportunities[PipelineStep],1)) >=2
)
)
RETURN
Revenue + ( Revenue * ( 'Opportunity Forecast Adjustment'[Forecast Adjustment Value] / 100 ) )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Revenue Open`

*Iterator: SUMX · Uses CALCULATE · Row filter*

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
CALCULATE(
SUMX(Opportunities, Opportunities[Value]),
FILTER(Opportunities, Opportunities[Status] = "Open")
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>
#### `Revenue Won`

*Iterator: SUMX · Uses CALCULATE · Row filter*

**Format:** `\$#,0.0;(\$#,0.0);\$#,0.0`

```dax
CALCULATE(
SUMX(Opportunities, Opportunities[Value]),
FILTER(Opportunities, Opportunities[Status] = "Won")
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

<details>
<summary>🔌 Power Query — 5 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `OpportunityTbl_Table` | navigation | ✅ |
| 3 | `#"Removed Other Columns"` | select_columns | ✅ |
| 4 | `#"Changed Type"` | type_cast | ✅ |
| 5 | `#"Renamed Columns"` | rename | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
OpportunityTbl_Table = Source{[Item="OpportunityTbl",Kind="Table"]}[Data],
#"Removed Other Columns" = Table.SelectColumns(OpportunityTbl_Table,{"OpportunitySeq", "CreatedonDate", "DaysToClose", "CloseDate", "SystemUserSeq", "Opportunity Owner Name", "AccountSeq", "ProductSeq", "ProductName", "CampaignSeq", "Campaign Name", "Budget", "Topic", "Purchase Process", "Decision Maker Identified", "Discount", "Value", "PipelineStep", "Probability (raw)", "Probability", "Rating", "Status"}),
#"Changed Type" = Table.TransformColumnTypes(#"Removed Other Columns",{{"OpportunitySeq", Int64.Type}, {"CreatedonDate", type date}, {"DaysToClose", Int64.Type}, {"CloseDate", type date}, {"SystemUserSeq", type text}, {"Opportunity Owner Name", type text}, {"AccountSeq", Int64.Type}, {"ProductSeq", Int64.Type}, {"ProductName", type text}, {"Budget", Int64.Type}, {"Topic", type text}, {"Purchase Process", type text}, {"Decision Maker Identified", type logical}, {"Discount", type number}, {"Value", Int64.Type}, {"PipelineStep", type text}, {"Probability (raw)", type number}, {"Probability", type number}, {"Rating", type text}, {"Status", type text}}),
#"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"CreatedonDate", "Opportunity Created On"}, {"ProductName", "Product Name"}})
in
#"Renamed Columns"
```

</details>

</details>

## Table: `Opportunity Calendar`

<details>
<summary>🧮 Calculated (DAX) · 9 cols — click to expand</summary>

> 🧮 **Calculated table** (DAX)

<details>
<summary>### Columns (9 visible, 6 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `DaySeq` | unknown |  | `0` | |
| `YEAR` | unknown |  | `0` | |
| `MONTH` | unknown |  |  | |
| `YEAR MONTH` | unknown |  |  | |
| `YEAR WEEK` | unknown |  |  | |
| `RELATIVE WEEK` | unknown |  |  | |
| `RELATIVE 07 DAY PERIOD` | unknown |  |  | |
| `RELATIVE 30 DAY PERIOD` | unknown |  |  | |
| `RELATIVE MONTH` | unknown |  | `0` | |
| `Date` | unknown |  | `Short Date` | ✗ |
| `DAY` | unknown |  | `Short Date` | ✗ |
| `MONTH NUMBER` | unknown |  | `0` | ✗ |
| `YEAR MONTH NUMBER` | unknown |  | `0` | ✗ |
| `WEEK` | unknown |  | `General Date` | ✗ |
| `RELATIVE DAY` | unknown |  | `General Date` | ✗ |

</details>

</details>

## Table: `Owners`

<details>
<summary>📥 Import · 2 cols · 1 measure · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (2 visible, 1 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Sales owner` | string |  |  | |
| `Manager` | string |  |  | |
| `SystemUserSeq` | int64 |  | `0` | ✗ |

</details>

### Measures

#### `Rev Goal`

*Uses variables · IF logic*

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
VAR RevenueInPipeline =
CALCULATE (
SUMX ( Opportunities, Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
&& VALUE(LEFT(Opportunities[PipelineStep],1)) >=3
)
)
VAR BaseGoal =
MROUND(([Revenue Won]+ (RevenueInPipeline*.75)),100000)
RETURN
IF(BaseGoal > 0, BaseGoal, MROUND(([Revenue Won]+ (RevenueInPipeline*.75)),10000))
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`]

🔗 **Depends on:** `[Revenue Won]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

<details>
<summary>🔌 Power Query — 6 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `OwnerTbl_Table` | navigation | ✅ |
| 3 | `#"Changed Type"` | type_cast | ✅ |
| 4 | `#"Removed Columns"` | remove_columns | ✅ |
| 5 | `#"Changed Type1"` | type_cast | ✅ |
| 6 | `#"Renamed Columns"` | rename | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
OwnerTbl_Table = Source{[Item="OwnerTbl",Kind="Table"]}[Data],
#"Changed Type" = Table.TransformColumnTypes(OwnerTbl_Table,{{"Owner", type text}, {"Factor", Int64.Type}}),
#"Removed Columns" = Table.RemoveColumns(#"Changed Type",{"Factor"}),
#"Changed Type1" = Table.TransformColumnTypes(#"Removed Columns",{{"SystemUserSeq", Int64.Type}}),
#"Renamed Columns" = Table.RenameColumns(#"Changed Type1",{{"Owner", "Sales owner"}})
in
#"Renamed Columns"
```

</details>

</details>

## Table: `Products`

<details>
<summary>📥 Import · 4 cols · Folding: — N/A — click to expand</summary>

> 📥 **Excel** (C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx → <File.Contents()>) *(parameterized)* · Query Folding: — N/A

<details>
<summary>### Columns (4 visible, 1 hidden — click to expand)</summary>

| Column | Type | Description | Format | Hidden |
|---|---|---|---|---|
| `Product category` | string |  |  | |
| `Product` | string |  |  | |
| `MinOppValue` | decimal |  | `\$#,0.###############;(\$#,0.###############);\$#,0.###############` | |
| `MaxOppValue` | decimal |  | `\$#,0.###############;(\$#,0.###############);\$#,0.###############` | |
| `ProductSeq` | int64 |  | `0` | ✗ |

</details>

<details>
<summary>🔌 Power Query — 5 steps</summary>

| # | Step | Type | Foldable |
|---|------|------|----------|
| 1 | `Source` | source | ✅ |
| 2 | `ProductTbl_Table` | navigation | ✅ |
| 3 | `#"Removed Columns"` | remove_columns | ✅ |
| 4 | `#"Changed Type"` | type_cast | ✅ |
| 5 | `#"Renamed Columns"` | rename | ✅ |

**Query Folding:** — Excel connector does not support query folding

**Full M Expression:**

```m
let
Source = Excel.Workbook(File.Contents("C:\Users\misewell\OneDrive - Microsoft\Documents\GitHub\ContosoBI\Contoso - Generic\Contoso - PowerBI Source Data.xlsx"), null, true),
ProductTbl_Table = Source{[Item="ProductTbl",Kind="Table"]}[Data],
#"Removed Columns" = Table.RemoveColumns(ProductTbl_Table,{"Factor"}),
#"Changed Type" = Table.TransformColumnTypes(#"Removed Columns",{{"ProductSeq", Int64.Type}, {"Product", type text}, {"Product LOB", type text}, {"MinOppValue", Currency.Type}, {"MaxOppValue", Currency.Type}}),
#"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"Product LOB", "Product category"}})
in
#"Renamed Columns"
```

</details>

</details>

## Measures Index (A–Z)

<details>
<summary>📋 22 measures — click to expand</summary>

#### `Case Count` · 📋 `Cases`

**Format:** `#,0`

```dax
COUNTROWS('Cases')
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Cases % by Product` · 📋 `Cases`

*Uses CALCULATE · Removes filters · Safe division*

**Format:** `0.00%;-0.00%;0.00%`

```dax
DIVIDE(
[Case Count],
CALCULATE(
[Case Count],All('Products')
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔗 **Depends on:** `[Case Count]`

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Products`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Cases % by Subject` · 📋 `Cases`

*Uses CALCULATE · Removes filters · Safe division*

**Format:** `0.0%;-0.0%;0.0%`

```dax
DIVIDE(
[Case Count],
CALCULATE(
[Case Count],All('Cases'[Subject])
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Subject`]

🔗 **Depends on:** `[Case Count]`

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Cases MoM%` · 📋 `Cases`

*Time intelligence · Uses CALCULATE · Uses variables · Safe division*

**Format:** `0.0%;-0.0%;0.0%`

```dax
VAR __PREV_MONTH = CALCULATE([Case Count], DATEADD('Case Calendar'[Date], -1, MONTH))
RETURN
DIVIDE([Case Count] - __PREV_MONTH, __PREV_MONTH)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Case Calendar`[`Date`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

🏷️ **Flags:** ⏱️ Time intelligence

</details>

---

#### `Close %` · 📋 `Opportunities`

*Division (check for zero)*

**Format:** `0.0%;-0.0%;0.0%`

```dax
[Count of Won]/([Count of Won]+[Count of Lost])
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

🔗 **Depends on:** `[Count of Won]`, `[Count of Lost]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Count of Lost` · 📋 `Opportunities`

*Preserves filters · Row filter*

**Format:** `#,0`

```dax
COUNTAX(
FILTER(
KEEPFILTERS(Opportunities),Opportunities[Status] = "Lost"
),
Opportunities[OpportunitySeq]
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Count of Won` · 📋 `Opportunities`

*Preserves filters · Row filter*

**Format:** `#,0`

```dax
COUNTAX(
FILTER(
KEEPFILTERS(Opportunities),Opportunities[Status] = "Won"
),
Opportunities[OpportunitySeq]
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`OpportunitySeq`], `Opportunities`[`Status`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `CSAT Impact` · 📋 `Cases`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Topic] <> SELECTEDVALUE ( 'Cases'[Topic] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`Topic`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `CSAT Impact - Agent` · 📋 `Cases`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Agent] <> SELECTEDVALUE ( 'Cases'[Agent] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Agent`], `Cases`[`CSAT`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `CSAT Impact - Products` · 📋 `Cases`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[ProductSeq] <> SELECTEDVALUE ( 'Cases'[ProductSeq] )  )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`ProductSeq`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `CSAT Impact - Subject` · 📋 `Cases`

*Uses variables · Division (check for zero)*

**Format:** `0.00%;-0.00%;0.00%`

```dax
VAR FactorAvg =
AVERAGE ( 'Cases'[CSAT] )
VAR AllAvg =
CALCULATE ( AVERAGE ( 'Cases'[CSAT] ), ALL ( 'Cases' ) )
VAR AllAvgExcept =
CALCULATE (
AVERAGE ( 'Cases'[CSAT] ),
FILTER ( ALL ( 'Cases' ), 'Cases'[Subject] <> SELECTEDVALUE ( 'Cases'[Subject] ) )
)
RETURN
1 - ( AllAvgExcept / AllAvg )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`CSAT`], `Cases`[`Subject`]

⚠️ **Filter removed (ALL/ALLEXCEPT):** `Cases`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Escalations` · 📋 `Cases`

*Uses CALCULATE · Safe division*

**Format:** `#,0%;-#,0%;#,0%`

```dax
DIVIDE(CALCULATE(COUNTROWS('Cases'),'Cases'[Is Escalated] = TRUE()) , [Case Count],0)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Is Escalated`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Forecast` · 📋 `Opportunities`

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
([Revenue Won]+[Revenue In Pipeline])
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

🔗 **Depends on:** `[Revenue Won]`, `[Revenue In Pipeline]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Forecast %` · 📋 `Opportunities`

*Division (check for zero)*

**Format:** `#,0%;-#,0%;#,0%`

```dax
(([Revenue Won]+[Revenue In Pipeline]))/ [Rev Goal]
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

🔗 **Depends on:** `[Revenue Won]`, `[Revenue In Pipeline]`, `[Rev Goal]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Forecast Adjustment Value` *(hidden)* · 📋 `Opportunity Forecast Adjustment`

```dax
SELECTEDVALUE('Opportunity Forecast Adjustment'[Forecast Adjustment], 0)
isHidden
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunity Forecast Adjustment`

🔎 **Columns:** `Opportunity Forecast Adjustment`[`Forecast Adjustment`]

❌ **Non-correlated:** `Accounts`, `Campaigns`, `Case Calendar`, `Cases`, `Contacts`, `Industries`, `Opportunities`, `Opportunity Calendar`, `Owners`, `Products`, `Territories`

</details>

---

#### `Opportunity Count` · 📋 `Opportunities`

**Format:** `#,0`

```dax
COUNTAX(Opportunities,TRUE())
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Opportunity Count In Pipeline` · 📋 `Opportunities`

*Aggregation: COUNT*

**Format:** `#,0`

```dax
CALCULATE (
COUNT( Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
--  && Opportunities[PipelineStep] IN { "3-Pipeline", "4-Mandate", "5-Close" }
)
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Rev Goal` · 📋 `Owners`

*Uses variables · IF logic*

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
VAR RevenueInPipeline =
CALCULATE (
SUMX ( Opportunities, Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
&& VALUE(LEFT(Opportunities[PipelineStep],1)) >=3
)
)
VAR BaseGoal =
MROUND(([Revenue Won]+ (RevenueInPipeline*.75)),100000)
RETURN
IF(BaseGoal > 0, BaseGoal, MROUND(([Revenue Won]+ (RevenueInPipeline*.75)),10000))
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`]

🔗 **Depends on:** `[Revenue Won]`

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Revenue In Pipeline` · 📋 `Opportunities`

*Uses variables · Division (check for zero)*

**Format:** `\$#,0.0;(\$#,0.0);\$#,0.0`

```dax
VAR Revenue =
CALCULATE (
SUMX ( Opportunities, Opportunities[Value] ),
FILTER (
Opportunities,
Opportunities[Status] = "Open"
&& VALUE(LEFT(Opportunities[PipelineStep],1)) >=2
)
)
RETURN
Revenue + ( Revenue * ( 'Opportunity Forecast Adjustment'[Forecast Adjustment Value] / 100 ) )
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`PipelineStep`], `Opportunities`[`Status`], `Opportunities`[`Value`], `Opportunity Forecast Adjustment`[`Forecast Adjustment Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Revenue Open` · 📋 `Opportunities`

*Iterator: SUMX · Uses CALCULATE · Row filter*

**Format:** `\$#,0.###############;(\$#,0.###############);\$#,0.###############`

```dax
CALCULATE(
SUMX(Opportunities, Opportunities[Value]),
FILTER(Opportunities, Opportunities[Status] = "Open")
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `Revenue Won` · 📋 `Opportunities`

*Iterator: SUMX · Uses CALCULATE · Row filter*

**Format:** `\$#,0.0;(\$#,0.0);\$#,0.0`

```dax
CALCULATE(
SUMX(Opportunities, Opportunities[Value]),
FILTER(Opportunities, Opportunities[Status] = "Won")
)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Opportunities`

🔎 **Columns:** `Opportunities`[`Status`], `Opportunities`[`Value`]

✅ **Compatible slicers:** `Accounts`, `Campaigns`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Case Calendar`, `Cases`, `Contacts`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

---

#### `SLA Compliance` · 📋 `Cases`

*Uses CALCULATE · Safe division*

**Format:** `#,0%;-#,0%;#,0%`

```dax
DIVIDE(CALCULATE(COUNTROWS('Cases'),'Cases'[Is SLA Violation] = FALSE()) , [Case Count],0)
```

<details>
<summary>🔗 Lineage — click to expand</summary>

📊 **Aggregates:** `Cases`

🔎 **Columns:** `Cases`[`Is SLA Violation`]

🔗 **Depends on:** `[Case Count]`

✅ **Compatible slicers:** `Accounts`, `Industries`, `Owners`, `Products`

❌ **Non-correlated:** `Campaigns`, `Case Calendar`, `Contacts`, `Opportunities`, `Opportunity Calendar`, `Opportunity Forecast Adjustment`, `Territories`

</details>

</details>

## Unused Columns

<details>
<summary>🔍 95 unreferenced columns — click to expand</summary>

| Table | Column | Type |
|-------|--------|------|
| `Accounts` | `Account Name` | string |
| `Accounts` | `Account Number` | string |
| `Accounts` | `AccountID` | string |
| `Accounts` | `AccountOwnerSeq` | int64 |
| `Accounts` | `Annual Revenue` | int64 |
| `Accounts` | `City` | string |
| `Accounts` | `Country` | string |
| `Accounts` | `Industry` | string |
| `Accounts` | `Industry Lookup` | unknown |
| `Accounts` | `Latitude` | double |
| `Accounts` | `Longitude` | double |
| `Accounts` | `Number of Employees` | int64 |
| `Accounts` | `Phone` | string |
| `Accounts` | `Postal Code` | string |
| `Accounts` | `Region` | string |
| `Accounts` | `State or Province` | string |
| `Accounts` | `Street` | string |
| `Accounts` | `Territory` | string |
| `Campaigns` | `Campaign Name` | string |
| `Campaigns` | `Factor` | int64 |
| `Campaigns` | `Type` | string |
| `Case Calendar` | `DAY` | unknown |
| `Case Calendar` | `DaySeq` | unknown |
| `Case Calendar` | `MONTH` | unknown |
| `Case Calendar` | `RELATIVE 07 DAY PERIOD` | unknown |
| `Case Calendar` | `RELATIVE 30 DAY PERIOD` | unknown |
| `Case Calendar` | `RELATIVE DAY` | int64 |
| `Case Calendar` | `RELATIVE MONTH` | unknown |
| `Case Calendar` | `RELATIVE WEEK` | unknown |
| `Case Calendar` | `WEEK` | unknown |
| `Case Calendar` | `Weekday` | unknown |
| `Case Calendar` | `YEAR` | unknown |
| `Case Calendar` | `YEAR MONTH` | unknown |
| `Case Calendar` | `YEAR WEEK` | unknown |
| `Cases` | `Activities` | int64 |
| `Cases` | `CSAT Goal` | unknown |
| `Cases` | `CSAT Label` | string |
| `Cases` | `CaseSeq` | int64 |
| `Cases` | `Escalations Goal` | unknown |
| `Cases` | `Minutes to First Contact` | int64 |
| `Cases` | `Origin` | string |
| `Cases` | `Resolution Minutes` | int64 |
| `Cases` | `Resolution Minutes Goal` | unknown |
| `Cases` | `SLA Compliance Goal` | unknown |
| `Cases` | `Severity` | string |
| `Cases` | `Status` | string |
| `Cases` | `Title` | string |
| `Contacts` | `City` | string |
| `Contacts` | `Contact` | string |
| `Contacts` | `ContactSeq` | int64 |
| `Contacts` | `Country` | string |
| `Contacts` | `FirstName` | string |
| `Contacts` | `Job Title` | string |
| `Contacts` | `LastName` | string |
| `Contacts` | `Latitude` | double |
| `Contacts` | `Longitude` | double |
| `Contacts` | `Phone` | string |
| `Contacts` | `Postal Code` | string |
| `Contacts` | `State or Province` | string |
| `Contacts` | `Street` | string |
| `Industries` | `Industry` | string |
| `Opportunities` | `Blank` | unknown |
| `Opportunities` | `Budget` | int64 |
| `Opportunities` | `Campaign Name` | string |
| `Opportunities` | `Days Remaining In Pipeline` | unknown |
| `Opportunities` | `DaysToClose` | int64 |
| `Opportunities` | `Decision Maker Identified` | boolean |
| `Opportunities` | `Discount` | double |
| `Opportunities` | `Opportunity Owner Name` | string |
| `Opportunities` | `Probability` | double |
| `Opportunities` | `Probability (raw)` | double |
| `Opportunities` | `Product Name` | string |
| `Opportunities` | `Purchase Process` | string |
| `Opportunities` | `Rating` | string |
| `Opportunities` | `Topic` | string |
| `Opportunities` | `Weeks Open` | unknown |
| `Opportunity Calendar` | `DaySeq` | unknown |
| `Opportunity Calendar` | `MONTH` | unknown |
| `Opportunity Calendar` | `RELATIVE 07 DAY PERIOD` | unknown |
| `Opportunity Calendar` | `RELATIVE 30 DAY PERIOD` | unknown |
| `Opportunity Calendar` | `RELATIVE MONTH` | unknown |
| `Opportunity Calendar` | `RELATIVE WEEK` | unknown |
| `Opportunity Calendar` | `YEAR` | unknown |
| `Opportunity Calendar` | `YEAR MONTH` | unknown |
| `Opportunity Calendar` | `YEAR WEEK` | unknown |
| `Owners` | `Manager` | string |
| `Owners` | `Sales owner` | string |
| `Products` | `MaxOppValue` | decimal |
| `Products` | `MinOppValue` | decimal |
| `Products` | `Product` | string |
| `Products` | `Product category` | string |
| `Territories` | `Country` | string |
| `Territories` | `Region` | string |
| `Territories` | `State Or Province Abbreviation` | string |
| `Territories` | `Territory` | string |

</details>

## Hidden Objects

<details>
<summary>🙈 3 hidden tables, 29 hidden columns — click to expand</summary>

### Hidden Tables

| Table |
|-------|
| `Industries` |
| `Opportunity Forecast Adjustment` |
| `Territories` |

### Hidden Columns

| Table | Column | Type |
|-------|--------|------|
| `Accounts` | `Account Owner` | string |
| `Accounts` | `AccountSeq` | int64 |
| `Accounts` | `IndustrySeq` | int64 |
| `Campaigns` | `CampaignSeq` | int64 |
| `Case Calendar` | `MONTH NUMBER` | unknown |
| `Case Calendar` | `WeekdaySeq` | unknown |
| `Case Calendar` | `YEAR MONTH NUMBER` | unknown |
| `Cases` | `AccountSeq` | int64 |
| `Cases` | `Case Created On` | dateTime |
| `Cases` | `ProductSeq` | int64 |
| `Cases` | `SystemUserSeq` | int64 |
| `Contacts` | `AccountSeq` | int64 |
| `Contacts` | `ContactID` | string |
| `Industries` | `IndustrySeq` | int64 |
| `Opportunities` | `AccountSeq` | int64 |
| `Opportunities` | `CampaignSeq` | string |
| `Opportunities` | `CloseDate` | dateTime |
| `Opportunities` | `Opportunity Created On` | dateTime |
| `Opportunities` | `ProductSeq` | int64 |
| `Opportunities` | `SystemUserSeq` | string |
| `Opportunity Calendar` | `DAY` | unknown |
| `Opportunity Calendar` | `Date` | unknown |
| `Opportunity Calendar` | `MONTH NUMBER` | unknown |
| `Opportunity Calendar` | `RELATIVE DAY` | unknown |
| `Opportunity Calendar` | `WEEK` | unknown |
| `Opportunity Calendar` | `YEAR MONTH NUMBER` | unknown |
| `Opportunity Forecast Adjustment` | `Forecast Adjustment` | unknown |
| `Owners` | `SystemUserSeq` | int64 |
| `Products` | `ProductSeq` | int64 |

</details>

---

*Generated by [pbi-semantic-doc](https://github.com/ViciusLio/pbi-semantic-doc) · 2026-03-18 07:44 UTC*

---

## Report

## Contents

- [Overview](#overview)
- [Visual Types Distribution](#visual-types-distribution) — 10 types
- [Custom Visuals](#custom-visuals) — 3 marketplace visuals
- [Bookmarks](#bookmarks) — 17 bookmarks
- [Advanced Metrics](#advanced-metrics)


## Overview

| | |
|---|---|
| Report Format | pbir |
| Total Pages | 3 (hidden: 0) |
| Total Visuals | 235 (avg 78.3/page, min 77, max 81) |
| Bookmarks | 17 |
| Report-Level Measures | 0 |
| **Complexity Index** | **🟡 48%** |

## Visual Types Distribution

<details>
<summary>📊 10 visual types across 235 visuals — click to expand</summary>

| Visual Type | Count | Percentage |
|---|---|---|
| actionButton | 193 | 82.1% |
| unknown | 12 | 5.1% |
| shape | 9 | 3.8% |
| textbox | 7 | 3.0% |
| barChart | 5 | 2.1% |
| image | 3 | 1.3% |
| custom | 3 | 1.3% |
| clusteredBarChart | 1 | 0.4% |
| slicer | 1 | 0.4% |
| lineChart | 1 | 0.4% |

</details>

## Custom Visuals

<details>
<summary>🔌 3 marketplace visuals — click to expand</summary>

- `decompositionTreeVisual`
- `keyDriversVisual`
- `qnaVisual`

</details>

## Bookmarks

<details>
<summary>🔖 17 bookmarks — click to expand</summary>

Total: 17

- Sales P - Funnel 1
- Key - Discount
- Last 12
- CSAT - KEY - High
- Services - KPI - Tabular
- Services - KPI - Chart
- Sales P - Chart 2
- Sales P - Tabular 2
- Service - SLA - Key Influencers
- Sales P - Chart 1
- CSAT - KEY - Low
- Key - Day to close
- CSAT - KEY - VS
- Services - KPI2 - Chart
- Service - KPI2 - Ribbon
- Last 90
- Service - SLA -PKPI

</details>

## Advanced Metrics

| Metric | Value |
|---|---|
| Pages with Drillthrough | 0 |
| Total Filters | 0 |
| Visuals with Mobile Layout | 37 |

---

*Generated by [pbi-semantic-doc](https://github.com/viciuslios/pbi-semantic-doc) · 2026-03-18 07:44 UTC*
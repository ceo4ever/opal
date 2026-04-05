# StatReport — NAVER Search Ad API

> 소스: https://naver.github.io/searchad-apidoc/#/tags/StatReport
> 캡처일: 2026-04-03 12:54
> 추출 방식: Playwright MCP
> 추출 모드: full

---

## Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| **list** | `GET /stat-reports` | Retrieves all of the registered Report Jobs |
| **get** | `GET /stat-reports/reportJobId` | Retrieves a registered Report Job |
| **create** | `POST /stat-reports` | Registers a Report Job |
| **delete** | `DELETE /stat-reports` | Delete Report Jobs |
| **delete** | `DELETE /stat-reports/reportJobId` | Deletes a Report Job |

---

## Stat Report Specification

### Ad Performance Report (reportTp: AD)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Media code | string | Media code |
| 9 | PC Mobile Type | string | PC Mobile Type |
| 10 | Impression | int | Impression count |
| 11 | Click | int | Click count |
| 12 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 13 | Sum of AD rank | int | Sum of AD rank, Average AD rank = Sum of AD rank / Impression |
| 14 | View count | int | Number of times that a video was viewed(including DOOH) |

### Ad Performance Detail Report (reportTp: AD_DETAIL)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Hours | string | Hours of basic date |
| 9 | Region code | string | Region code |
| 10 | Media code | string | Media code |
| 11 | PC Mobile Type | string | PC Mobile Type |
| 12 | Impression | int | Impression count |
| 13 | Click | int | Click count |
| 14 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 15 | Sum of AD rank | int | Sum of AD rank ,Average AD rank = Sum of AD rank / Impression |
| 16 | View count | int | Number of times that a video was viewed(including DOOH) |

### Ad Extension Performance Report (reportTp: ADEXTENSION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | AD extension ID | string | AD extension ID |
| 8 | AD extension Business Channel ID | string | Business Channel ID linked by AD extension |
| 9 | Media code | string | Media code |
| 10 | PC Mobile Type | string | PC Mobile Type |
| 11 | Impression | int | Impression count |
| 12 | Click | int | Click count |
| 13 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 14 | Sum of AD rank | int | Sum of AD rank , Average AD rank = Sum of AD rank / Impression |
| 15 | View count | int | Number of times that a video was viewed |

### Powerlink Search Term Report (reportTp: EXPKEYWORD)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | Search Keyword | string | Search Keyword |
| 6 | Media code | string | Media code |
| 7 | PC Mobile Type | string | PC Mobile Type |
| 8 | Search Keyword Type | int | 0,5:Exact, 1: Extend, 2: Close Variant |
| 9 | Impression | int | Impression count |
| 10 | Click | int | Click count |
| 11 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 12 | View count | int | Number of times that a video was viewed |

### Conversion Report (reportTp: AD_CONVERSION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Media code | string | Media code |
| 9 | PC Mobile Type | string | PC Mobile Type |
| 10 | Conversion Method | int | 1: Direct , 2:Indirect |
| 11 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 12 | Conversion count | int | Conversion count |
| 13 | Sales by conversion | long | Sales by conversion |

### Conversion Detail Report (reportTp: AD_CONVERSION_DETAIL)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Hours | string | Hours of basic date |
| 9 | Region code | string | Region code |
| 10 | Media code | string | Media code |
| 11 | PC Mobile Type | string | PC Mobile Type |
| 12 | Conversion Method | int | 1: Direct , 2:Indirect |
| 13 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 14 | Conversion count | int | Conversion count |
| 15 | Sales by conversion | long | Sales by conversion |

### Ad Extension Conversion Report (reportTp: ADEXTENSION_CONVERSION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | AD keyword ID | string | AD keyword ID |
| 6 | AD ID | string | AD ID |
| 7 | AD extension ID | string | AD extension ID |
| 8 | AD extension Business Channel ID | string | Business Channel ID linked by AD extension |
| 9 | Media code | string | Media code |
| 10 | PC Mobile Type | string | PC Mobile Type |
| 11 | Conversion Method | int | 1: Direct ,2:Indirect |
| 12 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 13 | Conversion count | int | Conversion count |
| 14 | Sales by conversion | long | Sales by conversion |

### Shopping Search Term Performance Detail Report (reportTp: SHOPPINGKEYWORD_DETAIL)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | Search keyword | string | Search Keyword |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Hours | string | Hours of basic date |
| 9 | Region code | string | Region code |
| 10 | Media code | string | Media code |
| 11 | PC Mobile Type | string | PC Mobile Type |
| 12 | Impression | int | Impression count |
| 13 | Click | int | Click count |
| 14 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 15 | Sum of AD rank | int | Sum of AD rank ,Average AD rank = Sum of AD rank / Impression |
| 16 | View count | int | Number of times that a video was viewed |

### Shopping Search Term Conversion Detail Report (reportTp: SHOPPINGKEYWORD_CONVERSION_DETAIL)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | Search keyword | string | Search Keyword |
| 6 | AD ID | string | AD ID |
| 7 | Business Channel ID | string | Business Channel ID |
| 8 | Hours | string | Hours of basic date |
| 9 | Region code | string | Region code |
| 10 | Media code | string | Media code |
| 11 | PC Mobile Type | string | PC Mobile Type |
| 12 | Conversion Method | int | 1: Direct , 2:Indirect |
| 13 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 14 | Conversion count | int | Conversion count |
| 15 | Sales by conversion | long | Sales by conversion |

### Shopping Brand Product Performance Report (reportTp: SHOPPINGBRANDPRODUCT)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | NV_MID | string | Unique key of Shopping Product |
| 6 | Business Channel ID | string | Business Channel ID |
| 7 | Media code | string | Media code |
| 8 | PC Mobile Type | string | PC Mobile Type |
| 9 | Impression | int | Impression count |
| 10 | Click | int | Click count |
| 11 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |
| 12 | View count | int | Number of times that a video was viewed |

### Shopping Brand Product Conversion Report (reportTp: SHOPPINGBRANDPRODUCT_CONVERSION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Campaign ID | string | Campaign ID |
| 4 | AD Group ID | string | AD Group ID |
| 5 | NV_MID | string | Unique key of Shopping Product |
| 6 | Business Channel ID | string | Business Channel ID |
| 7 | Media code | string | Media code |
| 8 | PC Mobile Type | string | PC Mobile Type |
| 9 | Conversion Method | int | 1: Direct , 2:Indirect |
| 10 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 11 | Conversion count | int | Conversion count |
| 12 | Sales by conversion | long | Sales by conversion |

### Criterion Performance Report (reportTp: CRITERION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Criterion id | string | Combining ownerId and dictionaryCode with the ~ character |
| 4 | PC Mobile Type | string | PC/Mobile |
| 5 | Impression | int | Impression count |
| 6 | Click | int | Click count |
| 7 | Cost | long | Cost(Data before March, 30, 2026 is provided as double) |

### Criterion Conversion Report (reportTp: CRITERION_CONVERSION)

| No | Property Name | Data Type | Description |
|----|--------------|-----------|-------------|
| 1 | Date | String | Basic date (ISO8601)) |
| 2 | CUSTOMER ID | int | CUSTOMER ID |
| 3 | Criterion id | string | Combining ownerId and dictionaryCode with the ~ character |
| 4 | PC Mobile Type | string | PC/Mobile |
| 5 | Conversion Method | int | 1: Direct, 2: Indirect |
| 6 | Conversion Type | string | (Data before July 3, 2024, is provided as integers) - purchase: Purchasing - sign_up: Subscription - add_to_cart: Cart - lead: Advance Purchase - custom001: Custom#1 - custom002: Custom#2 - custom003: Custom#3 - custom004: Custom#4 - custom005: Custom#5 - custom006: Custom#6 - custom007: Custom#7 - custom008: Custom#8 - custom009: Custom#9 - custom010: Custom#10 - add_to_wishlist: Wishlist - subscribe: Subscribe - schedule: Schedule - view_content: View content (Data before July 3, 2024 will be provided in the previous 5 types) 1: Purchasing, 2: Subscription, 3: Cart, 4: Advance purchase, 5: Others |
| 7 | Conversion count | int | Conversion count |
| 8 | Sales by conversion | long | Sales by conversion. |

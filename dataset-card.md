---
license: other
pretty_name: Humble Bundle Bundles
tags:
- humble-bundle
- games
- books
- software
size_categories:
- 1K<n<10K
configs:
- config_name: default
  data_files: "bundles-*.jsonl"
---

# Humble Bundle Bundles

Every bundle listed on the [Humble Bundle](https://www.humblebundle.com/bundles) bundles page, scraped daily since December 2024. The first file holds bundles that started in October 2024 and were still on sale.

There is one JSON Lines file per month, `bundles-YYYY-MM.jsonl`, holding the bundles that started that month. Each line is one bundle, identified by `machine_name`:

| Field | Contents |
| --- | --- |
| `author`, `basic_data` | Name, marketing blurbs, media type, description and end time of the bundle |
| `tier_item_data` | The items in the bundle keyed by their machine name, with publishers, developers, MSRP, minimum price, ratings and descriptions |
| `charity_data.charity_items` | The charities the bundle supports |
| `from_bundle` | The entry on the bundles listing, with its start and end dates and URL |
| `first_seen_at\|datetime`, `updated_at\|datetime` | When the scraper first saw the bundle, and when it last saw it change |

A bundle is updated in place while it stays on the listing, so files for recent months change from day to day.

Also available on [Kaggle](https://www.kaggle.com/datasets/ioexception/humble-scraping). The code that builds it lives at [fferegrino/humble-scraping](https://github.com/fferegrino/humble-scraping).

Bundle names, descriptions and artwork links belong to Humble Bundle and the respective publishers.

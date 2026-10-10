# Humble Bundle scraping

A dataset of the bundles on [humblebundle.com](https://www.humblebundle.com/bundles), scraped daily and published on [Hugging Face](https://huggingface.co/datasets/feregrino/humble-scraping) and [Kaggle](https://www.kaggle.com/datasets/ioexception/humble-bundles).

The data does not live in this repository. Each run of [dataset-sync](https://github.com/fferegrino/dataset-sync) downloads the current dataset from Hugging Face into `data/`, updates it with `humblebundle.py`, and uploads the result to Kaggle and then Hugging Face if any bundle changed. To read from Kaggle instead, run the workflow manually with `source: kaggle`.

`dataset-metadata.json` describes the Kaggle dataset and `dataset-card.md` becomes the Hugging Face dataset card.

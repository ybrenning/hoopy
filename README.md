# hooPY

Scraping NBA data from [Basketball Reference](https://www.basketball-reference.com) for use in personal projects

## Setup

### Install dependencies

```bash
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

### Scrape data

```bash
$ ./scrape.py -h

usage: scrape.py [-h] [--seasons seasons] stats [stats ...]

Scrape NBA data

positional arguments:
  stats              stat categories to scrape [totals, per_game, per_minute, per_poss, advanced, play-by-play, shooting,
                     adj_shooting]

options:
  -h, --help         show this help message and exit
  --seasons seasons  (optional) range of seasons to scrape from, e.g. 1996-1998
```

Currently, the scraping script can be used as a tool to fetch different kinds of NBA data.
The current implementation assumes the save directory to be `data/`.

### Example Usage

If one wanted to get player totals stats from 2000-2023:
```bash
$ ./scrape.py totals --seasons 2000-2023
```

> If no seasons argument gets passed, all seasons are fetched (1950-present)

Get multiple stat tables per season:
```bash
$ ./scrape.py totals advanced --seasons 2000-2023
```

Fetch a single season by making `start_season` and `end_season` the same:
```bash
$ ./scrape.py totals --seasons 2023-2023
```

These are the currently available stats and their keywords:

Player Stats:
* Totals (`totals`)
* Per Game (`per_game`)
* Per 36 Min (`per_minute`)
* Per 100 Poss (`per_poss`)
* Advanced (`advanced`)
* Play-by-Play (`play-by-play`)
* Shooting (`shooting`)
* Adjusted Shooting (`adj_shooting`)

Team Stats:
* Conference Standings (`standings`)

> Note that some stat categories such as `shooting` aren't available for older seasons, in this case the script will display a message and simply start at the first available season.

> Also keep in mind older seasons may have many missing columns for varying reasons (no block counting, no 3pt line, etc.)

### Run example dash app
(Or build your own)

```bash
$ python app.py
```

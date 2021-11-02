# Things I might do or plan on doing

## Performance

#### [Requests](https://blog.greendeck.co/beyond-requests/) 
- multithread and/or queue up requests
- reuse request sessions
- use DNS caching
- use a difference requests library

#### Parsing Responses
- use a bs4 alternative (lxml or direct string manipulation)
- multithread and/or queue up parsing

#### Database Access
- [x] save data in bulk
- queue up data saves
- use an alternative database (postgres, persistant redis, timescaledb)

## Integrity

#### Requests
- make use of user agents, cookies, headers to get blocked by less websites
- send requests through proxies to avoid getting blocked

#### Parsing Responses
- store link
- get all information possible (store the whole website)
- get just links from the website

#### Database Access
- make a simple database structure with as few fields as possible
- make a database structure that inherantly prevents duplicate records while preserving travel data(node duplicates, but no edge duplicates)

## Things I'm curious about that might impact flashgordon
- Scrapy

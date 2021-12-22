# Things I might do or plan on doing

## Performance

#### [Requests](https://blog.greendeck.co/beyond-requests/) 
- multiprocessing
- multithreading
- [x] reuse request sessions
- (tried to no improvement) use DNS caching
- use a difference requests library

#### Parsing Responses
- [x] use a bs4 alternative (lxml or direct string manipulation)
- multiprocessing
- multithread

#### Database Access
- [x] save data in bulk
- queue up data saves
- use an alternative database (postgres, persistant redis, timescaledb)

## Integrity

#### Requests
- make use of user agents, cookies, headers to get blocked by less websites
- send requests through proxies to avoid getting blocked

#### Parsing Responses
- [x] store link
- [x] get all information possible (store the whole website)
- [x] get just links from the website

#### Database Access
- [x] make a simple database structure with as few fields as possible
- [x] make a database structure that inherantly prevents duplicate records while preserving travel data(unique together constraint on point_a, point_b -> node duplicates, but no edge duplicates)

## Things I'm curious about that might impact flashgordon
- Scrapy

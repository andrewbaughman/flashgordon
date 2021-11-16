# flashgordon

speed. I am speed.

## Goals

The purpose of flashgordon is to gather useful data from the internet as quickly as possible.

A crawler will be ran to make get requests to URLs, parse the data from the response, and store relevant data.

As this goal is not a destination but rather a measure of improvement, the metrics used to measure progress will be Integrity and Performance.

### Integrity: By integrity, I mean completeness.
The data collected should be everything needed/useful, and the process used to collect it should be reliable, safe, and loving. 

Any changes made to the project should clearly improve its integrity.

### Performance: 
All processes within flashgordon should be fast and require as little work as possible to complete. 

Any changes made to flashgordon should measurably improve its performance.

## Installation and First crawl

1. Install postgres with `sudo apt install postgresql`
2. Start postgres with `systemctl services postgres start`
3. Create role and database
  1. `sudo su - postgres`
  2. `psql`
  3. `create role flash with login password ‘password’; grant all priveleges on database lighting_db to flash; alter database lighting_db owner to flash;`
4. Clone the repository
5. `pip3 install -r requirements.txt`
6. `pip3 install psycopg2` if it's not in the requirements
7. Configure postgres
8. `python3 manage.py migrate`
9. `python3 manage.py crawler`


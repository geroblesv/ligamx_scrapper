# Mediotiempo scrapper

This script scrapps mediotiempo.com and saves all the mexican football league results.

## Installation

```bash
pip install requirements.txt
```

## Usage

Once the results are fetched they are stored into a MYSQL local database, but once downloaded you can use whatever suits you.

## How it works

The script get all the seasons, then the matchdays (including playoffs), then the matches. It stores the scrapped url's in case you need to start the script again you don't duplicate the data.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

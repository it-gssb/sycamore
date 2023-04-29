class Definition:
    def __init__(self, name: str, index_col: str, url: str, iterate_over: str = None, data_location: str = None):
        self.name = name
        self.index_col = index_col
        self.url = url
        self.iterate_over = iterate_over
        self.data_location = data_location

    def __str__(self) -> str:
        return 'name={name}, index_col={index_col}, url={url}, iterate_over={iterate_over}, data_location={data_location}'.format(
                name=self.name,
                index_col=self.index_col,
                url=self.url,
                iterate_over=self.iterate_over,
                data_location=self.data_location
            )

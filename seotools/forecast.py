import pandas as pd
from prophet import Prophet


class Forecast:
    """
    Forecast traffic.

    Example:
        ```python
        from seotools.forecast import Forecast

        forecast = Forecast()
        data = forecast.forecast_search_console_attribute("data.csv", "Clicks")
        forecast.plot(data)
        forecast.plot_components(data)
        ```
    """

    def __init__(self) -> None:
        self.model = None
        pass

    def forecast_search_console_attribute(
        self, file_name: str, attribute: str, forecast_period: str = 30
    ) -> pd.DataFrame:
        """
        Forecast a search console attribute (i.e. Clicks or Impressions).
        """
        data = pd.read_csv(file_name)

        attribute = attribute.title()

        data = data[[attribute, "Date"]]

        # rename to ds and y, per the Prophet format
        data.columns = ["ds", "y"]

        model = Prophet()

        model.fit(data)

        self.model = model

        future = model.make_future_dataframe(periods=forecast_period)

        forecast = model.predict(future)

        return forecast

    def plot_forecast(self, forecast: pd.DataFrame) -> None:
        """
        Plot a forecast.
        """
        self.model.plot(forecast)

    def plot_components(self, forecast: pd.DataFrame) -> None:
        """
        See how the forecast applies in terms of a trend, daily differences, and seasonality.
        """
        self.model.plot_components(forecast)

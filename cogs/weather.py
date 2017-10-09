import discord

from discord.ext import commands


class Weather:

    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

        self.db = bot.db

        self.base_url = 'https://api.apixu.com'
        self.api_key = bot.credentials['apixu']

        self.rain_conditions = [
            'Mist',
            'Patchy rain nearby',
            'Light drizzle',
            'Patchy light rain',
            'Light rain',
            'Moderate rain at times',
            'Moderate rain',
            'Heavy rain at times',
            'Heavy rain',
            'Light rain shower',
            'Moderate or heavy rain shower',
            'Torrential rain shower',
            'Patchy rain possible'
        ]

        self.freezing_rain_conditions = [
            'Freezing drizzle',
            'Heavy freezing drizzle',
            'Light freezing rain',
            'Moderate or heavy freezing rain',
            'Light sleet',
            'Moderate or heavy sleet',
            'Ice pellets',
            'Light sleet showers',
            'Moderate or heavy sleet showers',
            'Light showers of ice pellets',
            'Moderate or heavy showers of ice pellets'
        ]

        self.snow_conditions = [
            'Patchy snow nearby',
            'Patchy sleet nearby',
            'Patchy freezing drizzle nearby',
            'Blowing snow',
            'Blizzard',
            'Patchy light snow',
            'Light snow',
            'Patchy moderate snow',
            'Moderate snow',
            'Patchy heavy snow',
            'Heavy snow',
            'Light snow showers',
            'Moderate or heavy snow showers'
        ]

        self.thunder_conditions = [
            'Thundery outbreaks in nearby',
            'Patchy light rain in area with thunder',
            'Moderate or heavy rain in area with thunder'
        ]

    @commands.group(invoke_without_command=True, name='weather')
    @commands.guild_only()
    async def _weather(self, ctx, *, location : str=None):
        """
        Shows the weather for the default location.

        Can also show weather for a specified location.
        """

        embed = discord.Embed()
        embed.color = 0xf7ff0f # nice yellow

        server_db = self.db.get(ctx.guild.id, {})
        weather = server_db.get('weather', {})
        forecast_days = weather.get('forecast_days', 1)
        default_loc = weather.get('default_loc', 'New York City')

        location = default_loc if not location else location
        location = location.replace(' ', '%20')

        terms = {
            'days' : forecast_days,
            'q' : f'\"{location}\"'
        }
        resp = await self.api_call(version='v1', call='forecast', terms=terms)
        if resp.get('error'):
            e_message = resp['error'].get('message', 'No error message.')
            embed.description = e_message
            await ctx.send(embed=embed)
            return

        units = server_db.get('units', 'imperial')

        temp_unit = '°F' if units == 'imperial' else '°C'
        dist_unit = 'miles' if units == 'imperial' else 'km'
        pres_unit = 'inches' if units == 'imperial' else 'mb'
        sped_unit = 'mph' if units == 'imperial' else 'kph'
        prec_unit = 'inches' if units == 'imperial' else 'mm'

        location = resp['location']
        current = resp['current']
        forecast = resp['forecast']['forecastday']

        name = location['name']
        region = location['region']

        current_temp = current['temp_f'] if units == 'imperial' else current['temp_c']
        current_windspeed = current['wind_mph'] if units == 'imperial' else current['wind_kph']
        current_winddir = current['wind_dir']
        current_pressure = current['pressure_in'] if units == 'imperial' else current['pressure_mb']
        current_precip = current['precip_in'] if units == 'imperial' else current['precip_mm']
        current_humidity = current['humidity']
        current_clouds = current['cloud']
        current_feelslike = current['feelslike_f'] if units == 'imperial' else current['feelslike_c']
        current_vis = current['vis_miles'] if units == 'imperial' else current['vis_km']
        last_updated = current['last_updated']
        current_condition = current['condition']['text']
        current_conditionimg = 'https://' + current['condition']['icon'].replace('\\', '').replace('//', '')

        temp_message = f'Actual: {current_temp}{temp_unit}\nFeels Like: {current_feelslike}{temp_unit}'
        wind_message = f'{current_windspeed} {sped_unit} {current_winddir}'
        other_message = f'Pressure: {current_pressure} {pres_unit}' \
                        f'\nPrecipitation: {current_precip} {prec_unit}' \
                        f'\nCloud Coverage: {current_clouds}%' \
                        f'\nVisibility: {current_vis} {dist_unit}'

        embed.title = f'Temperature for {name}, {region}'
        embed.description = f'Last updated: {last_updated}'
        embed.add_field(name='Temperature', value=temp_message)
        embed.add_field(name='Humidity', value=f'{current_humidity}%')
        embed.add_field(name='Wind Speed', value=wind_message)
        embed.add_field(name='Condition', value=current_condition)
        embed.add_field(name='Other', value=other_message)
        embed.set_thumbnail(url=current_conditionimg)

        for day in forecast:
            date = day['date']
            info = day['day']
            astro = day['astro']

            max_temp = info['maxtemp_f'] if units == 'imperial' else info['maxtemp_c']
            min_temp = info['mintemp_f'] if units == 'imperial' else info['mintemp_c']
            avg_temp = info['avgtemp_f'] if units == 'imperial' else info['avgtemp_c']
            maxwind = info['maxwind_mph'] if units == 'imperial' else info['maxwind_kph']
            totalprecip = info['totalprecip_in'] if units == 'imperial' else info['totalprecip_mm']
            avgvis = info['avgvis_miles'] if units == 'imperial' else info['avgvis_km']
            avghumidity = info['avghumidity']
            condition = info['condition']['text']

            if condition == 'Sunny':
                emoji = '\N{BLACK SUN WITH RAYS}'
            elif condition == 'Clear':
                emoji = '\N{FULL MOON SYMBOL}'
            elif condition.lower() == 'partly cloudy':
                emoji = '\N{WHITE SUN WITH SMALL CLOUD}'
            elif condition == 'Cloudy':
                emoji = '\N{WHITE SUN BEHIND CLOUD}'
            elif condition == 'Overcast':
                emoji = '\N{CLOUD}'
            elif condition == 'Fog':
                emoji = '\N{FOGGY}'
            elif condition == 'Freezing fog':
                emoji = '\N{FOGGY}\N{SNOWFLAKE}'
            elif condition == 'Patchy light drizzle':
                emoji= '\N{WHITE SUN BEHIND CLOUD WITH RAIN}'
            elif condition == 'Patchy light snow in area with thunder' or condition == 'Moderate or heavy snow in area with thunder':
                emoji = '\N{THUNDER CLOUD AND RAIN}\N{SNOWFLAKE}'
            elif condition in self.freezing_rain_conditions:
                emoji = '\N{CLOUD WITH RAIN}\N{SNOWFLAKE}'
            elif condition in self.rain_conditions:
                emoji = '\N{CLOUD WITH RAIN}'
            elif condition in self.snow_conditions:
                emoji = '\N{CLOUD WITH SNOW}'
            elif condition in self.thunder_conditions:
                emoji = '\N{THUNDER CLOUD AND RAIN}'
            else:
                emoji = '\N{BLACK QUESTION MARK ORNAMENT}'

            sunrise = astro['sunrise']
            sunset = astro['sunset']

            title = f'Forecast for ----- {date}'
            value = f'{emoji} {condition}, high of {max_temp}{temp_unit}, low of {min_temp}{temp_unit}, ' \
                    f'average temperature of {avg_temp}{temp_unit}, max wind speed of {maxwind} {sped_unit}, ' \
                    f'total precipitation of {totalprecip} {prec_unit}, average visibility of {avgvis} {dist_unit}, ' \
                    f'average humidity of {avghumidity}%\nSunrise: {sunrise}, sunset: {sunset}'

            embed.add_field(name=title, value=value)

        await ctx.send(embed=embed)

    @_weather.command(name='default')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def w_default(self, ctx, *, location=None):
        """Sets a default location for the weather command."""

        server_db = self.db.get(ctx.guild.id, {})
        weather = server_db.get('weather', {})
        default_loc = weather.get('default_loc')

        default_loc = location

        weather['default_loc'] = default_loc
        if not location:
            del weather['default_loc']

        server_db['weather'] = weather
        await self.db.put(ctx.guild.id, server_db)

        await ctx.send('👍')



    @_weather.command(name='forecastdays', aliases=['fdays'])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def w_fdays(self, ctx, days : int):
        """Set the amount of days to show forecasts for."""

        server_db = self.db.get(ctx.guild.id, {})
        weather = server_db.get('weather', {})
        db_days = weather.get('forecast_days', 1)

        if days < 1 or days > 5:
            await ctx.send('Forecast days cannot exceed 5 days or be under 1 day.')
            return

        db_days = days
        weather['forecast_days'] = db_days
        server_db['weather'] = weather
        await self.db.put(ctx.guild.id, server_db)

        await ctx.send('👍')



    async def api_call(self, version, call, terms):

        url = f'{self.base_url}/{version}/{call}.json?key={self.api_key}'

        for term in terms:
            url += f'&{term}={terms[term]}'

        async with self.session.get(url) as rawdata:
            return await rawdata.json()


def setup(bot):
    bot.add_cog(Weather(bot))

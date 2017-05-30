import discord
import asyncio
import datetime

from random import randint


class Racing:

    def __init__(self, bot, message : discord.Message, users: list, car_people: list=[], comet_people: list=[]):
        self.bot = bot

        self.users = users

        self.message = message
        self.channel = message.channel

        self.horse_emoji = '\N{HORSE RACING}'
        self.car_emoji = '\N{RACING CAR}'
        self.comet_emoji = '\N{COMET}'

        self.car_people = car_people
        self.comet_people = comet_people

        self.rand_step = 4
        self.car_step = 6
        self.comet_step = 15

        self.track_length = 30

        self.positions = {}
        self.tracks = {}

        self.active = False

    def get_track_embed(self):
        """Gets the initial embed for the track."""

        embed = discord.Embed()
        embed.colour = 0x019608

        embed.title = 'Horse Racing'

        for i, user in enumerate(self.users):

            if user.id in self.car_people:
                track = self.car_emoji + ('-' * (self.track_length - 1))
            elif user.id in self.comet_people:
                track = self.comet_emoji + ('-' * (self.track_length - 1))
            else:
                track = self.horse_emoji + ('-' * (self.track_length - 1))

            name = user.nick if user.nick is not None else user.name

            name = f'{name}\'s Horse'

            embed.add_field(name=name, value='|' + track + '|', inline=False)
            self.tracks[user.id] = track
            self.positions[user.id] = 0

        return embed

    def move_horse(self, index):
        """Randomly moves a horse on the track."""

        uid = list(self.positions.keys())[index]

        old_pos = self.positions[uid]

        if uid in self.car_people:
            step = randint(3, self.car_step)
        elif uid in self.comet_people:
            step = randint(7, self.comet_step)
        else:
            step = randint(0, self.rand_step)

        self.positions[uid] += step

        if self.positions[uid] < 0:
            self.positions[uid] = 0

        new_pos = self.positions[uid]

        track_list = list(self.tracks[uid])

        track_list[old_pos] = '-'

        try:
            if uid in self.car_people:
                track_list[new_pos] = self.car_emoji
            elif uid in self.comet_people:
                track_list[new_pos] = self.comet_emoji
            else:
                track_list[new_pos] = self.horse_emoji
        except IndexError:
            new_pos = self.track_length - 1
            if uid in self.car_people:
                track_list[new_pos] = self.car_emoji
            elif uid in self.comet_people:
                track_list[new_pos] = self.comet_emoji
            else:
                track_list[new_pos] = self.horse_emoji

        self.tracks[uid] = ''.join(track_list)

        return self.tracks[uid]

    async def start_racing(self):
        """Sends the racetrack and begins the race."""

        em = self.get_track_embed()
        self.game_board = await self.channel.send(embed=em)

        self.start_time = datetime.datetime.now()

        self.active = True

    def check_for_winner(self):
        """Checks all the horses for a winner."""

        winners = []

        for uid, pos in self.positions.items():
            if pos >= self.track_length-1:
                winners.append(uid)

        return winners

    async def end_racing(self, winners : list):
        """End the race when somebody wins."""

        self.active = False
        endtime = datetime.datetime.now()

        delta = endtime - self.start_time
        seconds = round(delta.total_seconds(), 2)

        members = self.message.guild.members
        winner_objs = [discord.utils.get(members, id=uid) for uid in winners]

        winner_names = [m.name for m in winner_objs]

        try:
            await self.game_board.delete()
        except discord.NotFound:
            pass

        await self.channel.send(content=f'{seconds} seconds\nWinner(s): ' + ', '.join(winner_names))

    async def update_track(self):
        """Updates the track."""

        embed = self.game_board.embeds[0]

        for i, field in enumerate(embed.fields):
            val = self.move_horse(i)

            embed.set_field_at(i, name=field.name, value='|' + val + '|', inline=False)

        try:
            await self.game_board.edit(content=' ', embed=embed)
        except discord.NotFound:
            self.game_board = await self.channel.send(embed=embed)

    async def start(self):
        """Handles the loop for the race."""

        await self.start_racing()

        while self.active:
            await asyncio.sleep(3)
            await self.update_track()
            winners = self.check_for_winner()
            if winners:
                await self.end_racing(winners)

import datetime
from discord.ext import commands
from html import unescape
import random

import question


class DB(commands.Cog):
    def __init__(self, bot):
        self.conn = bot.pool

    # async def get_tossups(self, **params):
    #     query = "select tossups.id, tossups.text, tossups.formatted_answer, c.name, t.name from tossups " \
    #             "join tournaments t on tossups.tournament_id = t.id join categories c on tossups.category_id = c.id where "
    #     if params.get("q_id"):
    #         query += "tossups.id=$1"
    #     else:
    #         query += f"{'c.category_id=$'}c.category_id="

    async def get_tossups(self, category=None, number=1, difficulty=random.choice([2, 3, 4, 5]), q_id=None):
        if q_id:
            data = await self.conn.fetch(
                "select tossups.id, tossups.text, tossups.formatted_answer, c.name, t.name from tossups "
                "join tournaments t on tossups.tournament_id = t.id join categories c on tossups.category_id = c.id "
                "where tossups.id=$1", q_id)
        elif not category:
            data = await self.conn.fetch(
                "select tossups.id, tossups.text, tossups.formatted_answer, categories.name, tournaments.name from tossups "
                "join tournaments on tossups.tournament_id = tournaments.id and tournaments.difficulty = {0} "
                "join categories on tossups.category_id = categories.id "
                # "WHERE tossups.formatted_answer like '%<strong>%' or position(' ' in formatted_answer) <= 0 "
                # "or tossups.formatted_answer similar to '[a-zA-Z]+\s<[^strong^em^u>^b>]%'"
                "ORDER BY RANDOM() LIMIT {1}".format(difficulty, number))
        else:
            data = await self.conn.fetch(
                "select tossups.id, tossups.text, tossups.formatted_answer, categories.name, tournaments.name from tossups "
                "join tournaments on tossups.tournament_id = tournaments.id and tournaments.difficulty = {0} "
                "join categories on tossups.category_id = categories.id "
                "WHERE (tossups.formatted_answer like '%<strong>%' or position(' ' in formatted_answer) <= 0 "
                "or tossups.formatted_answer similar to '[a-zA-Z]+\s<[^strong^em^u>^b>]%') "
                "and tossups.category_id = {1}"
                "ORDER BY RANDOM() LIMIT {2}".format(difficulty, category, number))
        data = data[0]

        return question.Tossup(data[0], unescape(data[1]), unescape(data[2]), data[3], data[4],
                               "(*)" in unescape(data[1]))

    async def get_bonuses(self, number=1):
        data = await self.conn.fetch(
            "with A2 as (select bonuses.id, tournaments.name, leadin, bonuses.category_id from bonuses "
            "join tournaments on bonuses.tournament_id=tournaments.id and tournaments.difficulty in (2,3,4,5)) "
            "select leadin, array_agg(bonus_parts.text order by bonus_parts.id), "
            "array_agg(bonus_parts.formatted_answer order by bonus_parts.id) as ans, "
            "categories.name, A2.name from bonus_parts join A2 on bonus_parts.bonus_id = A2.id "
            "join categories on A2.category_id = categories.id "
            "group by categories.name, A2.name, bonus_id, leadin "
            "having (array_agg(bonus_parts.formatted_answer))[1] like '%<strong>%' "
            "or (position(' ' in (array_agg(bonus_parts.formatted_answer))[1]) <= 0 "
            "and position(' ' in (array_agg(bonus_parts.formatted_answer))[2]) <= 0 "
            "and position(' ' in (array_agg(bonus_parts.formatted_answer))[3]) <= 0) "
            "order by random() limit {}".format(number))
        data = data[0]
        return question.Bonus(data[0], [unescape(x) for x in data[1]], [unescape(x) for x in data[2]], data[3], data[4])

    async def get_ms(self, number=1):
        data = await self.conn.fetch(
            "select tossups.id, tossups.text, tossups.formatted_answer, categories.name, tournaments.name from tossups "
            "join tournaments on tossups.tournament_id = tournaments.id and tournaments.difficulty = 1 "
            "join categories on tossups.category_id = categories.id "
            "order by random() limit {}".format(number))
        data = data[0]
        return question.Tossup(data[0], unescape(data[1]), unescape(data[2]), data[3], data[4],
                               "(*)" in unescape(data[1]))

    async def get_player_settings(self, user):
        data = await self.conn.fetch("select categories, difficulties from player_settings where user_id=$1", user.id)
        return (None, None) if not data else data[0]

    async def log_tossup(self, question_obj: question.Tossup, ctx, in_tournament):
        return await self.conn.fetchval("insert into tossup_calls (question_id, caller_id, guild_id, channel_id, "
                                        "has_power) values ($1, $2, $3, $4, $5) returning id", question_obj.id,
                                        ctx.author.id if not in_tournament else -1, ctx.guild.id, ctx.channel.id,
                                        question_obj.power)

    async def log_buzz(self, pk_id, message, percent):
        """"Logs a row in the database representing the buzz. After the user answers, this row will be updated
        by update_buzz"""
        time = datetime.datetime.now()
        return await self.conn.fetchval("insert into buzzes (call_id, user_id, percent_through, time) "
                                        "values ($1, $2, $3, $4) returning id", pk_id, message.author.id, percent, time)

    async def update_buzz(self, buzz_id, correct: bool, points=0):
        await self.conn.execute("update buzzes set correct = $1, points = $2 where id = $3", correct, points, buzz_id)

    async def set_difficulty(self, user, difficulties):
        print(difficulties)
        exists = await self.conn.fetchval("select exists(select * from player_settings where user_id=$1)", user.id)
        if exists:
            print(difficulties)
            await self.conn.execute("update player_settings set difficulties=$1 where user_id=$2",
                                    difficulties, user.id)
        else:
            await self.conn.execute("insert into player_settings (user_id, difficulties) values ($1, $2)",
                                    user.id, difficulties)

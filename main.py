import discord
from discord.ext import commands
import packet_handling
import random
from fuzzywuzzy import fuzz
import asyncio
import config
import time
from typing import List

bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
questionlist = packet_handling.get_questions()
groups = []
teams = []
players = []


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def ping():
    await bot.say("pong!")


class Group:
    def __init__(self, name, members):
        self.name = name
        self.members = members


class Team:
    def __init__(self, server, name, captain, members, score=0):
        # self.group = group
        self.server = server
        self.name = name
        self.captain = captain
        self.members = members
        self.score = score

    def __str__(self):
        return self.name


class Player:
    def __init__(self, member, server, score=0):
        self.member = member
        self.server = server
        self.score = score  # not used for any data/analysis, just per-game score

    def __str__(self):
        return str(self.member.name)

    def fuckme(self):
        return str(self.member.name)

@bot.command(name="group", pass_context=True)
async def group_(ctx, name):
    if any(each_group.name == name for each_group in groups):
        await bot.say("That group already exists!")
        return
    groups.append(Group(name, [ctx.message.author]))
    await bot.say('New group "{0}" created! Type !join {0} to join!'.format(name))


@bot.command(pass_context=True)
async def mygroup(ctx):
    group = get_group(ctx.message.author)
    if group is not None:
        await bot.say(group.name)
    else:
        await bot.say("You're not in a team.")


def get_group(member):
    for group in groups:
        if member in group.members:
            return group
    return None


def get_team(member: discord.Member, server):
    for team in teams:
        for player in team.members:
            if member == player.member and server == player.server:
                return team
    return None


def get_player(member, server):
    for team in teams:
        for player in team.members:
            if member == player.member and server == player.server:
                return player


def serialize_team(teamname, server):
    for team in teams:
        if team.name == teamname and team.server == server:
            return team


@bot.command(name="team", pass_context=True, aliases=["maketeam", "newteam"])
async def team_(ctx, name):
    if any(each_team.name == name for each_team in teams):
        await bot.say("That team already exists!")
        return
    if get_team(ctx.message.author, ctx.message.server) is not None:
        await bot.say("You're already in a team.")
        return
    else:
        player = Player(ctx.message.author, ctx.message.server)
        players.append(player)
    team = Team(ctx.message.server, name, ctx.message.author, [])
    team.members.append(player)
    print(player)
    teams.append(team)
    await bot.say('New team "{0}" created! Type !join {0} to join!'.format(name))


@bot.command(name="teams", pass_context=True, aliases=["listteams", "allteams"])
async def teams_(ctx):
    teams_in_server = [team for team in teams if team.server == ctx.message.server]
    if teams_in_server:
        team_list = 'Current teams in {0}:\n'.format(ctx.message.server) + ''.join(
            sorted(':small_blue_diamond:' + team.name + '\n' for team in teams_in_server))
        await bot.say(team_list)
    else:
        await bot.say("No teams have been made in this server yet!")


@bot.command(pass_context=True)
async def myteam(ctx):
    team = get_team(ctx.message.author, ctx.message.server)
    if team is not None:
        await bot.say(team.name)
    else:
        await bot.say("You're not in a team.")


@bot.command(name="captain", pass_context=True)
async def captain_(ctx, new_captain: discord.Member=None):
    team = get_team(ctx.message.author, ctx.message.server)
    if team is not None:
        if new_captain is None:
            await bot.say("{0} is the captain of your team, {1}".format(team.captain, team.name))
            return
        if team.captain == ctx.message.author:
            if get_player(new_captain, ctx.message.server) in team.members:
                team.captain = new_captain
                await bot.say("New team captain of {0}: {1}".format(team, new_captain))
            else:
                await bot.say("{0} isn't in your team!".format(new_captain))
        else:
            await bot.say("You aren't captain of {0}".format(team.name))
    else:
        await bot.say("You're not in a team!")


@bot.command(pass_context=True)
async def join(ctx, name):
    for team in teams:
        if team.name == name:
            player = Player(ctx.message.author, ctx.message.server)
            team.members.append(player)
            await bot.say("{0} joined the team {1}!".format(ctx.message.author, name))
            return
    await bot.say("That doesn't seem to be a team!")


@bot.command(pass_context=True, aliases=['leaveteam'])
async def leave(ctx, name=None):
    member_team = get_team(ctx.message.author, ctx.message.server)
    if name is None:
        if member_team is None:
            await bot.say("You're not in a team.")
            return

    if member_team is not None and (member_team.name == name or name is None):
        if len(member_team.members) == 1:
            await bot.say("You're the last person in the team!\nLeaving the team has deleted it. You can always create "
                          "a new one with !team <team name>.")
            teams.remove(member_team)
            return
        if ctx.message.author == member_team.captain:
            await bot.say(
                "You're the captain of {0}! You should defer captainship to one of your teammates with !captain @user.\nTeam members:\n".format(
                    member_team) + "".join([":small_blue_diamond:" + str(member) + "\n" for member in member_team.members]))
            return
        member_team.members.remove(get_player(ctx.message.author, ctx.message.server))
        await bot.say("Left {0}!".format(name))
        return

    await bot.say("You're not in a team by that name.")


@bot.command(pass_context=True)
async def tournament(ctx, *, teams_in_game=None):
    caller_team = get_team(ctx.message.author, ctx.message.server)
    if caller_team is None:
        await bot.say("You should make or join a team first.")
        return
    if caller_team.captain != ctx.message.author:
        await bot.say("You can't start a tournament unless you're a team captain.")
        return
    if teams_in_game is None:
        await bot.say("Please enter the teams that will be playing in this tournament, "
                      "separated by spaces")
        msg = await bot.wait_for_message(author=ctx.message.author)
        team_names = msg.content.split(" ")
    else:
        team_names = teams_in_game.split(" ")
    if len(team_names) < 2:
        await bot.say("You must have at least 2 teams to have a tournament!")
        return
    teams_in_game = []
    for teamname in team_names:
        teams_in_game.append(serialize_team(teamname, ctx.message.server))
    for team in teams_in_game:
        if team not in teams:
            await bot.say("{0} isn't a team. Make sure to check your spelling! Teams currently "
                          "in this server are:\n".format(team)
                          + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
            return

    await bot.say("Would you like bonus questions? Answer with yes or no.")
    msg = await bot.wait_for_message(author=ctx.message.author)
    if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
        bonus = True
        await bot.say("Bonus questions will be read.")
    else:
        bonus = False
        await bot.say("Bonus questions will not be read.")
    await bot.say("How many tossup questions do you want (default is 20)?")
    msg = await bot.wait_for_message(author=ctx.message.author)
    num_of_questions = int(msg.content)
    await bot.say("Tournament starting! Your setup is as follows:\n"
                  "Teams competing: " + ", ".join([t_.name for t_ in teams_in_game]) +
                  "\nNumber of tossups: " + str(num_of_questions) +
                  "\nBonus questions: " + str(bonus) +
                  "\nIf this is correct, type yes. If you'd like to edit something, type teams, tossups, or bonuses.")

    def check2(message):
        return message.content in ["yes", "y", "ye", "yeet", "teams", "tossups", "bonuses"]

    msg = await bot.wait_for_message(author=ctx.message.author, check=check2)
    if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
        await bot.say("Tournament starting! Good luck!")
    # TODO
    elif msg.content.lower() == "teams":
        await bot.say("Alright, re-enter the list of teams competing, separated by spaces")
        msg = await bot.wait_for_message(author=ctx.message.author)
        teams_in_game = msg.content.split(" ")
        if teams_in_game.count() < 2:
            await bot.say("You must have at least 2 teams to have a tournament!")
            return
        for team in teams_in_game:
            if team not in [t.name for t in teams]:
                await bot.say("{0} isn't a team. Make sure to check your spelling! Teams currently "
                              "in this server are:\n".format(team)
                              + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
                return
    elif msg.content.lower() == "tossups":
        await bot.say("Alright, re-enter the number of tossups you want.")
        msg = await bot.wait_for_message(author=ctx.message.author)
        num_of_questions = int(msg.content)
    elif msg.content.lower() == "bonuses":
        await bot.say("Alright, re-renter yes or no if you want bonuses or not.")
        msg = await bot.wait_for_message(author=ctx.message.author)
        if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
            bonus = True
            await bot.say("Bonus questions will be read.")
        else:
            bonus = False
            await bot.say("Bonus questions will not be read.")
    playerlist = []
    for t in teams_in_game:
        print(t.members)
        playerlist += t.members
    print(playerlist)
    for i in range(num_of_questions):
        await read_question(bonus, playerlist)
    teams_in_game.sort(reverse=True, key=lambda x: x.score)
    await bot.say("Tournament over! Final leaderboard:\n" +
                  "".join([":small_blue_diamond:" + t.name + ": " + str(t.score) + " points!\n" for t in teams_in_game]))
    

async def read_question(bonus: bool, playerlist):
    print([str(player) for player in playerlist])
    correct = False
    skip = False
    neggers = []
    question_obj = random.choice(questionlist)
    question_arr = question_obj.question.split(" ")
    sent_question = await bot.say(" ".join(question_arr[:5]))
    await asyncio.sleep(1)
    for i in range(1, question_arr.__len__() // 5 + 1):
        sent_question_content = sent_question.content
        sent_question = await bot.edit_message(sent_question,
                                               sent_question_content + " " + " ".join(question_arr[i * 5:i * 5 + 5]))
        print(sent_question.content)

        def check(message):
            return get_player(message.author, message.server) in playerlist and message.author not in neggers and "buzz" in message.content

        msg = None
        msg = await bot.wait_for_message(timeout=1, check=check)
        if msg is not None:
            await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
            answer = await bot.wait_for_message(timeout=10, author=msg.author)
            if answer is not None:
                ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                if ratio > 75:
                    await bot.say("correct!")
                    print("correct! ratio: " + str(ratio))
                    correct = True
                    await bot.edit_message(sent_question, question_obj.question)
                    team = get_team(msg.author, msg.author.server)
                    player = get_player(msg.author, msg.author.server)
                    team.score += 20
                    player.score += 20
                    break
                else:
                    await bot.say("incorrect!")
                    print("incorrect")
                    msg = None
                    sent_question = await bot.say(sent_question_content)
            else:
                await bot.say("Time's up!")
                await asyncio.sleep(1)
    wait_time = 10
    if not correct:
        while wait_time > 0:
            timer = time.time()
            msg = None
            msg = await bot.wait_for_message(timeout=int(wait_time), check=check)
            wait_time = time.time() - timer
            if msg is not None:
                await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                answer = None
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                if answer is not None:
                    ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                    if ratio > 75:
                        await bot.say("correct!")
                        print("correct! ratio: " + str(ratio))
                        correct = True
                        team = get_team(msg.author, msg.author.server)
                        player = get_player(msg.author, msg.author.server)
                        team.score += 20
                        player.score += 20
                        break
                    else:
                        await bot.say("incorrect!")
                        print("incorrect")
                else:
                    await bot.say("Time's up!")
                    await asyncio.sleep(1)

        if not correct:
            await bot.say("The answer is {0}!".format(question_obj.answer))

    neggers.clear()


@bot.command(pass_context=True)
async def question(ctx, num=1):
    correct = False
    skip = False
    user = ctx.message.author
    wrong_buzzers = []
    for j in range(0, num):

        question_obj = random.choice(questionlist)

        # reading_task = bot.loop.create_task(read_question(question_obj))

        # loop.run_until_complete(asyncio.ensure_future(read_question(question_obj), loop=loop))
        question_arr = question_obj.question.split(" ")
        sent_question = await bot.say(" ".join(question_arr[:5]))
        await asyncio.sleep(1)
        for i in range(1, question_arr.__len__() // 5 + 1):
            sent_question_content = sent_question.content
            sent_question = await bot.edit_message(sent_question, sent_question_content + " " + " ".join(question_arr[i*5:i*5+5]))
            print(sent_question.content)

            def check(message):
                return message.author not in wrong_buzzers and "buzz" in message.content
            msg = None
            msg = await bot.wait_for_message(timeout=1)
            if msg is not None:
                if "buzz" in msg.content:
                    await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                    answer = await bot.wait_for_message(timeout=10, author=msg.author)
                    ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                    if ratio > 80:
                        await bot.say("correct!")
                        print("correct! ratio: " + str(ratio))
                        correct = True
                        msg = None
                        break
                    else:
                        await bot.say("incorrect!")
                        if answer.author not in wrong_buzzers:
                            wrong_buzzers.append(answer.author)
                        print("incorrect")
                        msg = None
                        sent_question = await bot.say(sent_question_content)
                elif "skip" in msg.content:
                    skip = True
                    print("skip!")
                    break

        if not skip:
            msg = await bot.wait_for_message(timeout=10, check=check)
            if msg is not None:
                await bot.say("buzz from {0}! 10 seconds to answer".format(msg.author))
                answer = await bot.wait_for_message(timeout=10, author=msg.author)
                ratio = fuzz.ratio(answer.content.lower(), question_obj.answer.lower())
                if ratio > 80:
                    await bot.say("correct!")
                    print("correct! ratio: " + str(ratio))
                    correct = True
                else:
                    await bot.say("incorrect!")
                    print("incorrect")
            if not correct:
                await bot.say("The answer is {0}!".format(question_obj.answer))
            msg = None
            msg = await bot.wait_for_message(timeout=20, content="next")
            if msg is None:
                return

        wrong_buzzers.clear()
        print(question_obj.answer)
        print(question_obj.packet)


bot.run(config.token)

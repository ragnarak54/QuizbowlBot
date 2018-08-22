import discord
from discord.ext import commands
import packet_handling
import random
from fuzzywuzzy import fuzz
import asyncio
import config

bot = commands.Bot(command_prefix=['!', '?'], description="Quiz bowl bot!")
questionlist = packet_handling.get_questions()
groups = []
teams = []


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
    def __init__(self, server, name, captain, members):
        # self.group = group
        self.server = server
        self.name = name
        self.captain = captain
        self.members = members


class Player:
    def __init__(self, member, server, team, score=0):
        self.member = member
        self.server = server
        self.team = team
        self.score = score  # not used for any data/analysis, just per-game score


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


def get_team(member):
    for team in teams:
        if member in team.members:
            return team
    return None


@bot.command(name="team", pass_context=True, aliases=["maketeam", "newteam"])
async def team_(ctx, name):
    if any(each_team.name == name for each_team in teams):
        await bot.say("That team already exists!")
        return
    '''found_group = get_group(ctx.message.author)
    if found_group is None:
        await bot.say("You must be in a group to create a team!")
        return'''
    if get_team(ctx.message.author) is not None:
        await bot.say("You're already in a team.")
        return
    teams.append(Team(ctx.message.server, name, ctx.message.author, [ctx.message.author]))
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
    team = get_team(ctx.message.author)
    if team is not None:
        await bot.say(team.name)
    else:
        await bot.say("You're not in a team.")


@bot.command(name="captain", pass_context=True)
async def captain_(ctx, new_captain: discord.Member=None):
    team = get_team(ctx.message.author)
    if team is not None:
        if new_captain is None:
            await bot.say("{0} is the captain of your team, {1}".format(team.captain, team.name))
            return
        if team.captain == ctx.message.author:
            if new_captain in team.members:
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
            team.members.append(ctx.message.author)
            await bot.say("Joined the team {0}!".format(name))
            return
    await bot.say("That doesn't seem to be a team!")


@bot.command(pass_context=True, aliases=['leaveteam'])
async def leave(ctx, name):
    member_team = get_team(ctx.message.author)
    if member_team is not None and member_team.name == name:
        if len(member_team.members) == 1:
            await bot.say("You're the last person in the team!\nLeaving the team has deleted it. You can always create"
                          "a new one with !team <team name>.")
            teams.remove(member_team)
            return
        if ctx.message.author == member_team.captain:
            await bot.say(
                "You're the captain of {0}! You should defer captainship to one of your teammates with !captain @user.\nTeam members:\n".format(
                    member_team) + "".join([":small_blue_diamond:" + member + "\n" for member in member_team.members]))
            return
        member_team.members.remove(ctx.message.author)
        await bot.say("Left {0}!".format(name))
        return

    await bot.say("You're not in a team by that name.")


@bot.command(pass_context=True)
async def tournament(ctx):
    await bot.say("")


async def read_question():
    correct = False
    skip = False


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

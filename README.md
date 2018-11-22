# Quizbowl Bot

This is a bot for Discord that can be used to play [Quizbowl](https://www.naqt.com/about/quiz-bowl.html)!

## Getting Started

Add me as a friend on Discord @ragnarak54#9413, and I'll help you invite the bot to your server!

## Using the bot

Here's how to use all of the bot's commands

### Casual playing

```
?tossup
```

is the most basic command. The bot will start reading a question, and anyone in that channel can buzz at any time when they know the answer. You buzz simply by typing "buzz". Just like in quizbowl, wait to be recognized for your buzz to avoid giving a free answer to someone who buzzed in right before you! For ease of access, you can also type `?q, ?t, or ?question`

If you're studying up on a certain category, you can put it after the tossup command, or any of its shortcuts, like `?q literature` (or even `?q lit`!) to get a tossup from that category.

```
?bonus
```

Similar to `?tossup`, this command starts a bonus question. It's different in that only you can answer the questions. Staying true to real-life quizbowl, you don't buzz for bonuses. Simply wait until each part is done being read, and then type your answer. Shortcut `?b` also calls this command.

### Tournament play

If you want to play with points and teams, then the first thing you need to do is make a team. Use

```
?team <teamname>
```

to make a team with name teamname. Other people can join your team with `?join <teamname>` and leave it with `?leave`.
Once your teams are set, use the 

```
?tournament
```

command to start the tournament dialogue. Choose your setting for bonuses and number of questions, then it begins!


## Built With

* [Python](https://www.python.org/)
* [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper for Python
* [postgreSQL](https://www.postgresql.org/) - Database used
* [Digital Ocean](https://www.digitalocean.com/) - Sever hosting service
* [QuizDB](https://quizdb.org) - Question database

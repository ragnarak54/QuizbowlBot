import psycopg2
import config


def get_tossups(number=50):
    conn = psycopg2.connect("dbname={0} user={1} password={2} host={3}".format(config.mysql['db'], config.mysql['user'],
                                                                               config.mysql['passwd'],
                                                                               config.mysql['host']))
    cursor = conn.cursor()
    cursor.execute("select categories.name, tossups.text, tossups.formatted_answer from tossups join tournaments on "
                   "tossups.tournament_id = tournaments.id and tournaments.difficulty in (2,3,4,5) "
                   "join categories on tossups.category_id = categories.id "
                   "ORDER BY RANDOM() LIMIT {}".format(number))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_bonuses(number=50):
    conn = psycopg2.connect("dbname={0} user={1} password={2} host={3}".format(config.mysql['db'], config.mysql['user'],
                                                                               config.mysql['passwd'],
                                                                               config.mysql['host']))
    cursor = conn.cursor()
    cursor.execute("with A2 as (select bonuses.id, leadin, bonuses.category_id from bonuses join tournaments "
                   "on bonuses.tournament_id = tournaments.id and tournaments.difficulty in (2,3,4,5)) "
                   "select categories.name, leadin, array_agg(bonus_parts.text order by bonus_parts.id), "
                   "array_agg(bonus_parts.formatted_answer order by bonus_parts.id) "
                   "from bonus_parts join A2 on bonus_parts.bonus_id = A2.id "
                   "join categories on A2.category_id = categories.id "
                   "group by categories.name, bonus_id, leadin order by random() limit {}".format(number))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

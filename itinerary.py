from datetime import datetime
from unicodedata import category
# from test import Category, locations,current_user
from pydantic import BaseModel, Field
import location
import datetime
import users

class Preferences(BaseModel):
    byCar: bool
    lunch: bool
    dinner: bool
    onlyFree: bool
    withPet:bool
    data: datetime.date
    time: datetime.time
    categories: list[location.Category]

class Itinerary(BaseModel):
    morning: list[location.Location]
    lunch: list[location.Location]
    afternoon: list[location.Location]
    dinner: list[location.Location]
    night: list[location.Location]

def full_score_of(loc):
    weights = {
        "age"       : 0.25,
        "distance"  : 0.25,
        "rain"      : 0.5,
        "likes"     : 0.5
    }
    def calc_age(user_age, lowest, highest):
        if user_age >= lowest and user_age <= highest:
            return 1.0
        diff = min(lowest - user_age, user_age - highest)
        return (1.0 - (diff / 100.0)) * weights["age"]
    def calc_likes(id):
        return location.all_likes_for(id) / location.all_likes() * weights["likes"]
    def calc_weather(id):
        return 0
    return calc_age(users.current_user.age, loc.ages[0], loc.ages[1]) + calc_likes(loc.id) + calc_weather(loc)

def make_itinerary(prefs: Preferences):
    day = prefs.data.weekday()
    # visit_time = prefs.time.hour
    visit_time = 0

    def is_open(loc, start, end):
        return loc.opening_times[day].hour <= start and loc.closing_times[day].hour >= end

    filters = [
        lambda loc: True if not prefs.onlyFree else prefs.onlyFree and loc.price == 0,
        lambda loc: loc.category in prefs.categories,
        lambda loc: True if not prefs.withPet else prefs.withPet and loc.with_pets,
        lambda loc: is_open(loc, visit_time, 23)
    ]
    ok = [ loc for loc in location.locations if all([ f(loc) for f in filters ]) ]

    def prepare_internal(hours, duration, restaurantOnly = False):
        locs  = [(x, full_score_of(x)) for x in ok if is_open(x, hours[0], hours[1]) and not x.durata > duration]
        locs  = [ x for x in locs if x[0].category==location.Category.RESTORATION ] if restaurantOnly else locs
        if restaurantOnly:
            print(len(locs))
        if len(locs) == 0:
            return []
        locs.sort(key = lambda x: x[1], reverse=True)
        return [ x[0] for x in locs[0:min(3, len(locs))] ]

    def prepare(hours, duration, restaurantOnly = False):
        nonlocal ok
        l = prepare_internal(hours, duration, restaurantOnly)
        ok = filter(lambda x: x not in l, ok)
        #ok = ok2
        return l


    launch    = prepare([10, 12], 2, restaurantOnly=True)
    dinner    = prepare([16, 22], 6, restaurantOnly=True)

    morning   = prepare([10, 12], 2)
    afternoon = prepare([12, 18], 6)
    evening   = prepare([18, 22], 4)

    return Itinerary (
        morning     = morning,
        lunch       = launch,
        afternoon   = afternoon,
        dinner      = dinner,
        night       = evening
    )

"""
def tests():
    location.load_likes()
    location.load_locations()
    i = make_itinerary(Preferences(
        byCar       = True,
        lunch       = True,
        dinner      = True,
        onlyFree    = False,
        withPet     = False,
        data        = datetime.date(2022, 1, 1),
        time        = datetime.time(15, 0),
        categories  = location.all_categories()
    ))
    print(i.json())

tests()
"""

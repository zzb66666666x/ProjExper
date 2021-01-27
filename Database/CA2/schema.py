# this file is for defining the rules of accessing data from tuples
class Info:
    def __init__(self, prim_key = None, attr_val = None):
        self.key = prim_key     # positions for the primary key, may be a tuple
        self.attr = attr_val    # positions for the indexes of attributes

def eval_key_string(key):
    if key is None:
        return None
    if type(key) is str:
        return key
    if type(key) is int:
        return key
    if type(key) is tuple or type(key) is list:
        temp = ""
        for i in key:
            if type(i) == int:
                i = str(i)
            temp += i
        return temp
    return int(key)

def get_key_person(data):
    if data is None:
        return None
    return data[0]

def get_key_movie(data):
    if data is None:
        return None
    return (data[0], data[1])

def get_key_restriction(data):
    if data is None:
        return None
    return (data[0], data[1], data[2], data[3])

def get_key_role(data):
    if data is None:
        return None
    return (data[0], data[1], data[2])

def get_key_actor_award(data):
    if data is None:
        return None
    return (data[0], data[1], data[2],data[3], data[4], data[5], data[6])

def get_key_award(data):
    if data is None:
        return None
    return (data[0], data[1], data[2])

def get_key_director(data):
    if data is None:
        return None
    return (data[0], data[1], data[2])

def get_key_writer(data):
    if data is None:
        return None
    return (data[0], data[1], data[2], data[3])

def get_info(name, attribute):
    # name can be a tuple of names
    # return the indexes to locate the attributes in the data
    try:
        dictionary = relation_schema[name]
    except KeyError:
        return None
    key_pos = dictionary["key_idx"]
    schema = dictionary["schema"]
    info = Info()
    info.key = key_pos
    if type(attribute) is str:
        # print("guess what")
        # print(schema)
        # print(attribute)
        info.attr = schema.index(attribute)
    elif type(attribute) is list or type(attribute) is tuple:
        ans = []
        for i in attribute:
            pos = schema.index(i)
            ans.append(pos)
        info.attr = ans
    return info

relation_schema = {"PERSON":{"schema":("PERSON_id", "PERSON_first_name", "PERSON_last_name", "PERSON_year"), "key_idx": 0},
                   "ROLE":{"schema":("ROLE_id", "ROLE_movie", "ROLE_year", "ROLE_description", "ROLE_credits"), "key_idx": [0,1,2]},
                   "MOVIE":{"schema":("MOVIE_title", "MOVIE_year", "MOVIE_country", "MOVIE_runtime", "MOVIE_genre"), "key_idx": [0,1]},
                   "RESTRICTION": {"schema": ("RESTRICTION_title", "RESTRICTION_year", "RESTRICTION_description", "RESTRICTION_country"), "key_idx":[0,1,2,3]},
                   "ACTOR_AWARD":{"schema":("ACTOR_AWARD_title","ACTOR_AWARD_M_year","ACTOR_AWARD_description","ACTOR_AWARD_name","ACTOR_AWARD_year","ACTOR_AWARD_category","ACTOR_AWARD_result"),"key_idx":[0,1,2,3,4,5,6]},
                   "AWARD":{"schema":("AWARD_name","AWARD_institution","AWARD_country"),"key_idx":[0,1,2]},
                   "DIRECTOR":{"schema":("DIRECTOR_id","DIRECTOR_title","DIRECTOR_year"),"key_idx":[0,1,2]},
                   "WRITER":{"schema":("WRITER_id","WRITER_title","WRITER_year","WRITER_credits"),"key_idx":[0,1,2,3]}}

get_key_table = {"PERSON":get_key_person,
                 "ROLE": get_key_role,
                 "MOVIE": get_key_movie,
                 "RESTRICTION": get_key_restriction,
                 "ACTOR_AWARD":get_key_actor_award,
                 "AWARD":get_key_award,
                 "DIRECTOR":get_key_director,
                 "WRITER":get_key_writer}

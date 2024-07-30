from domain.entities import *
from infrastructure.database.orm import *

def to_user_group_domain(orm: UserGroupORM) -> UserGroup:
    return UserGroup(
        id=orm.id,
        user_id=orm.user_id,
        group_id=orm.group_id
    )
    
def to_character_domain(orm: CharacterORM) -> Character:
    return Character(
        id=orm.id,
        name=orm.name,
        pool_name=orm.pool_name,
        image_name=orm.image_name,
        image_path=orm.image_path
    )
    
def to_ug_character_domain(orm: UGCharacterORM) -> UGCharacter:
    return UGCharacter(
        id=orm.id,
        user_group_id=orm.user_group_id,
        character_id=orm.character_id,
        acquisition_time=orm.acquisition_time
    )
    
def to_stats_domain(orm: StatsORM) -> Stats:
    return Stats(
        id=orm.id,
        user_group_character_id=orm.user_group_character_id,
        user_group_id=orm.user_group_id,
        character_id=orm.character_id,
        lastest_acquisition_time=orm.lastest_acquisition_time,
        draw_count=orm.draw_count,
        acquired_by_ex_count=orm.acquired_by_ex_count,
        acquired_by_ntr_count=orm.acquired_by_ntr_count,
        mating_count=orm.mating_count,
        divorce_count=orm.divorce_count
    )

def to_current_domain(orm: CurrentORM) -> CurrentUGC:
    return CurrentUGC(
        id=orm.id,
        user_group_id=orm.user_group_id,
        character_id=orm.character_id,
        update_time=orm.update_time
    )

def to_single_domain(orm: SingleORM) -> SingleEvent:
    return SingleEvent(
        id=orm.id,
        user_group_id=orm.user_group_id,
        character_id=orm.character_id,
        event_type=orm.event_type,
        result=orm.result,
        event_time=orm.event_time
    )
    
def to_double_domain(orm: DoubleORM) -> DoubleEvent:
    return DoubleEvent(
        id=orm.id,
        group_id=orm.group_id,
        action_initiator_user_group_id=orm.action_initiator_user_group_id,
        action_receiver_user_group_id=orm.action_receiver_user_group_id,
        initiator_current_character_id=orm.initiator_current_character_id,
        receiver_current_character_id=orm.receiver_current_character_id,
        event_type=orm.event_type,
        result=orm.result,
        event_time=orm.event_time
    )
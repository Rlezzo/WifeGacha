from domain.entities import *
from infrastructure.database.orm import *

def to_user_group_orm(domain: UserGroup) -> UserGroupORM:
    return UserGroupORM(
        id=domain.id,
        user_id=domain.user_id,
        group_id=domain.group_id
    )
    
def to_character_orm(domain: Character) -> CharacterORM:
    return CharacterORM(
        id=domain.id,
        name=domain.name,
        pool_name=domain.pool_name,
        image_name=domain.image_name,
        image_path=domain.image_path
    )
    
def to_ug_character_orm(domain: UGCharacter) -> UGCharacterORM:
    return UGCharacterORM(
        id=domain.id,
        user_group_id=domain.user_group_id,
        character_id=domain.character_id,
        acquisition_time=domain.acquisition_time
    )
    
def to_stats_orm(domain: Stats) -> StatsORM:
    return StatsORM(
        id=domain.id,
        user_group_character_id=domain.user_group_character_id,
        user_group_id=domain.user_group_id,
        character_id=domain.character_id,
        lastest_acquisition_time=domain.lastest_acquisition_time,
        draw_count=domain.draw_count,
        acquired_by_ex_count=domain.acquired_by_ex_count,
        acquired_by_ntr_count=domain.acquired_by_ntr_count,
        mating_count=domain.mating_count,
        divorce_count=domain.divorce_count
    )
    
def to_current_orm(domain: CurrentUGC) -> CurrentORM:
    return CurrentORM(
        id=domain.id,
        user_group_id=domain.user_group_id,
        character_id=domain.character_id,
        update_time=domain.update_time
    )

def to_single_orm(domain: SingleEvent) -> SingleORM:
    return SingleORM(
        id=domain.id,
        user_group_id=domain.user_group_id,
        character_id=domain.character_id,
        event_type=domain.event_type,
        result=domain.result,
        event_time=domain.event_time
    )
    
def to_double_orm(domain: DoubleEvent) -> DoubleORM:
    return DoubleORM(
        id=domain.id,
        group_id=domain.group_id,
        action_initiator_user_group_id=domain.action_initiator_user_group_id,
        action_receiver_user_group_id=domain.action_receiver_user_group_id,
        initiator_current_character_id=domain.initiator_current_character_id,
        receiver_current_character_id=domain.receiver_current_character_id,
        event_type=domain.event_type,
        result=domain.result,
        event_time=domain.event_time
    )
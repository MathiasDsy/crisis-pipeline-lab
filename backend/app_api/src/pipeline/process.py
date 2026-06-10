from crisis_geo.domain.models import Tweet, Event, ProcessResult
from crisis_geo.modules.relevance import is_tweet_relevant
from crisis_geo.modules.extraction import extract_locations
from crisis_geo.modules.geocoding import geocode_location
from crisis_geo.modules.event_matching import (
    find_matching_event,
    create_event,
    add_tweet_to_event,
)



def process_tweet(tweet: Tweet, events: list[Event]) -> ProcessResult:
    """
    Orchestrates the full tweet processing pipeline.
    """

    # 1. Relevance filtering
    if not is_tweet_relevant(tweet.text):
        return ProcessResult(
            status="ignored",
            tweet_id=tweet.id,
            reason="Tweet is not relevant",
        )

    # 2. Location extraction
    locations = extract_locations(tweet.text)
    print(f"Extracted locations: {locations}")


    if not locations:
        return ProcessResult(
            status="uncertain",
            tweet_id=tweet.id,
            reason="No location found",
        )

    # 3. Source location selection
    # V1 naive: take the first detected location.
    source_location = locations[0]

    # 4. Geocoding 
    point = geocode_location(source_location)

    if point is None:
        return ProcessResult(
            status="uncertain",
            tweet_id=tweet.id,
            reason=f"Could not geocode location: {source_location.name}",
        )

    # 5. Event matching
    matched_event = find_matching_event(
        point=point,
        events=events,
        max_distance_km=20.0,
    )

    if matched_event is not None:
        add_tweet_to_event(matched_event, tweet.id)

        return ProcessResult(
            status="assigned",
            tweet_id=tweet.id,
            event_id=matched_event.id,
            location=point,
            reason="Assigned to existing event",
        )

    # # 6. Event creation
    new_event = create_event(
        point=point, #TODO change en vrai géolocalisation
        tweet_id=tweet.id,
    )

    events.append(new_event)

    return ProcessResult(
        status="created",
        tweet_id=tweet.id,
        event_id=new_event.id,
        location=point, #TODO change en vrai géolocalisation
        reason="Created new event",
    )
from src.components.components import (
    RelevanceClassifierComponent,
    LocationExtractorComponent,
    GeocoderComponent,
    EventMatcherComponent,
)

COMPONENT_REGISTRY = {
    "relevance_classifier": RelevanceClassifierComponent,
    "location_extractor": LocationExtractorComponent,
    "geocoder": GeocoderComponent,
    "event_matcher": EventMatcherComponent,
}
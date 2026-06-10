from src.pipeline.components.relevance.transformer_classifier import RelevanceClassifierComponent
from src.pipeline.components.extraction.location_extractor import LocationExtractorComponent
from src.pipeline.components.geocoding.photon_geocoder import PhotonGeocoderComponent
from src.pipeline.components.event_matching.event_matcher import EventMatcherComponent


COMPONENT_REGISTRY = {
    "relevance.transformer_classifier": RelevanceClassifierComponent,
    "extraction.location_extractor": LocationExtractorComponent,
    "geocoding.photon": PhotonGeocoderComponent,
    "event.matching": EventMatcherComponent,
}
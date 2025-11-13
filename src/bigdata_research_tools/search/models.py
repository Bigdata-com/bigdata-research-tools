from bigdata_client.models.entities import QueryComponentMixin
from pydantic import BaseModel


class BigdataEntity(BaseModel):
    id: str
    name: str
    volume: int | None = None
    description: str | None = None
    entity_type: str
    company_type: str | None = None
    country: str | None = None
    sector: str | None = None
    industry_group: str | None = None
    industry: str | None = None
    ticker: str | None = None
    webpage: str | None = None
    isin_values: list[str] | None = None
    cusip_values: list[str] | None = None
    sedol_values: list[str] | None = None
    listing_values: list[str] | None = None
    product_type: str | None = None
    product_owner: str | None = None
    organization_type: str | None = None
    position: str | None = None
    employer: str | None = None
    nationality: str | None = None
    gender: str | None = None
    place_type: str | None = None
    region: str | None = None
    landmark_type: str | None = None
    # Fields for concepts that are not covered above
    entity_type_name: str | None = None
    concept_level_2: str | None = None
    concept_level_3: str | None = None
    concept_level_4: str | None = None
    concept_level_5: str | None = None

    @classmethod
    def from_sdk(cls, sdk_entity: QueryComponentMixin) -> "BigdataEntity":
        assert getattr(sdk_entity, "id", None) is not None, (
            "SDK entity must have an 'id' attribute"
        )
        assert getattr(sdk_entity, "name", None) is not None, (
            "SDK entity must have a 'name' attribute"
        )
        return cls(
            id=getattr(sdk_entity, "id", None),
            name=getattr(sdk_entity, "name", None),
            volume=getattr(sdk_entity, "volume", None),
            description=getattr(sdk_entity, "description", None),
            entity_type=getattr(sdk_entity, "entity_type", None),
            company_type=getattr(sdk_entity, "company_type", None),
            country=getattr(sdk_entity, "country", None),
            sector=getattr(sdk_entity, "sector", None),
            industry_group=getattr(sdk_entity, "industry_group", None),
            industry=getattr(sdk_entity, "industry", None),
            ticker=getattr(sdk_entity, "ticker", None),
            webpage=getattr(sdk_entity, "webpage", None),
            isin_values=getattr(sdk_entity, "isin_values", None),
            cusip_values=getattr(sdk_entity, "cusip_values", None),
            sedol_values=getattr(sdk_entity, "sedol_values", None),
            listing_values=getattr(sdk_entity, "listing_values", None),
            product_type=getattr(sdk_entity, "product_type", None),
            product_owner=getattr(sdk_entity, "product_owner", None),
            organization_type=getattr(sdk_entity, "organization_type", None),
            position=getattr(sdk_entity, "position", None),
            employer=getattr(sdk_entity, "employer", None),
            nationality=getattr(sdk_entity, "nationality", None),
            gender=getattr(sdk_entity, "gender", None),
            place_type=getattr(sdk_entity, "place_type", None),
            region=getattr(sdk_entity, "region", None),
            landmark_type=getattr(sdk_entity, "landmark_type", None),
            entity_type_name=getattr(sdk_entity, "entity_type_name", None),
            concept_level_2=getattr(sdk_entity, "concept_level_2", None),
            concept_level_3=getattr(sdk_entity, "concept_level_3", None),
            concept_level_4=getattr(sdk_entity, "concept_level_4", None),
            concept_level_5=getattr(sdk_entity, "concept_level_5", None),
        )

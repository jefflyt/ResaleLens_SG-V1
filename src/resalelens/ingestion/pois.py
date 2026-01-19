"""POI ingestion from OneMap API."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..models import POI, POIType
from .onemap_client import OneMapClient
from .utils import log_ingestion_run

def ingest_pois(session: Session) -> dict[str, int]:
    """
    Ingest Points of Interest (POIs) from OneMap using Search.

    Args:
        session: Database session

    Returns:
        Summary of ingestion statistics
    """
    client = OneMapClient()
    
    # Map POIType to Search Terms
    search_terms = {
        POIType.MRT: ["MRT Station"], 
        POIType.LRT: ["LRT Station"],
        POIType.SUPERMARKET: ["Supermarket", "NTUC FairPrice", "Cold Storage", "Sheng Siong", "Giant"],
        POIType.CLINIC: ["Clinic", "Polyclinic"], 
        POIType.PARK: ["Park", "Garden"],
        POIType.MALL: ["Shopping Centre", "Mall", "Plaza"],
        POIType.HAWKER: ["Hawker Centre", "Food Centre", "Market"],
        POIType.SCHOOL: ["Primary School", "Secondary School", "Junior College"],
    }
    
    summary = {
        "fetched": 0,
        "inserted": 0,
        "errors": 0,
        "warnings": 0
    }

    with log_ingestion_run(session, "pois") as run:
        print("Starting POI ingestion from OneMap (Search API)...")
        
        for poi_type, terms in search_terms.items():
            for term in terms:
                print(f"Searching for: '{term}' ({poi_type})...")
                records = client.fetch_poi_search(term)
                summary["fetched"] += len(records)
                
                batch = []
                # Use set to avoid duplicates within this batch
                seen_in_batch = set() 
                
                for record in records:
                    try:
                        name = record.get("SEARCHVAL") or record.get("BUILDING") or record.get("ADDRESS")
                        lat = record.get("LATITUDE")
                        lon = record.get("LONGITUDE")

                        if not name or not lat or not lon or lat == "NIL" or lon == "NIL":
                            continue
                            
                        # Normalize name: Title Case
                        name = name.title()
                            
                        key = (name, float(lat), float(lon))
                        if key in seen_in_batch:
                            continue
                        seen_in_batch.add(key)
                        
                        batch.append({
                            "poi_type": poi_type,
                            "name": name,
                            "latitude": float(lat),
                            "longitude": float(lon),
                            # "last_updated" handled by DB default
                        })
                        
                    except Exception:
                        summary["errors"] += 1
                        continue

                # Filter duplicates against DB
                # Since we don't have unique constraint, check memory again (efficient for <10k POIs)
                if batch:
                    # Get existing for this type to minimize query size
                    existing_query = select(POI.latitude, POI.longitude, POI.name).where(POI.poi_type == poi_type)
                    existing = session.execute(existing_query).all()
                    existing_set = {(float(r.latitude), float(r.longitude), r.name) for r in existing}
                    
                    new_records = []
                    for item in batch:
                        if (item["latitude"], item["longitude"], item["name"]) not in existing_set:
                            # Double check against existing_set to prevent adding same POI twice if OneMap returns it for multiple search terms
                            # (e.g. "Mall" and "Plaza" might return same building)
                            # Actually, existing_set comes from DB. 
                            # But if "Supermarket" search returns "X" and "FairPrice" search returns "X", we need to dedupe across loops?
                            # Optimally, yes. But here we do it per term. 
                            # Safe enough: if DB has it, we skip. If DB doesn't, we add. 
                            # Ideally we should maintain a `global_seen` set for the transaction.
                            new_records.append(item)
                            # Update existing set so next term loop sees it
                            existing_set.add((item["latitude"], item["longitude"], item["name"]))
                    
                    if new_records:
                        session.execute(insert(POI), new_records)
                        summary["inserted"] += len(new_records)
        
        print(f"POI Ingestion Complete: {summary}")
        run.rows_processed = summary["inserted"]
        
    return summary

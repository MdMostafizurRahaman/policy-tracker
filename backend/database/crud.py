from typing import Dict, List, Optional
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from ..models.policy_models import FormSubmission, PolicyInitiative

async def insert_submission(collection: AsyncIOMotorCollection, submission: FormSubmission) -> str:
    submission_dict = submission.dict()
    result = await collection.insert_one(submission_dict)
    return str(result.inserted_id)

async def get_submission(collection: AsyncIOMotorCollection, submission_id: str) -> Optional[Dict]:
    submission = await collection.find_one({"_id": ObjectId(submission_id)})
    return submission

async def update_submission_status(collection: AsyncIOMotorCollection, submission_id: str, status: str) -> bool:
    result = await collection.update_one(
        {"_id": ObjectId(submission_id)},
        {"$set": {"submission_status": status, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0

async def get_pending_submissions(collection: AsyncIOMotorCollection, skip: int, limit: int) -> List[Dict]:
    cursor = collection.find(
        {"submission_status": {"$in": ["pending", "partially_approved"]}}
    ).sort("created_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]

async def update_policy_status(
    collection: AsyncIOMotorCollection,
    submission_id: str,
    policy_index: int,
    status: str,
    admin_notes: str = ""
) -> bool:
    update_dict = {
        f"policyInitiatives.{policy_index}.status": status,
        f"policyInitiatives.{policy_index}.admin_notes": admin_notes,
        "updated_at": datetime.utcnow()
    }
    result = await collection.update_one(
        {"_id": ObjectId(submission_id)},
        {"$set": update_dict}
    )
    return result.modified_count > 0
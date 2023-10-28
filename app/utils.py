import uuid
from app.models import ReferralOffer

def generate_referral_link(user):
    existing_offer = ReferralOffer.objects.filter(referrer=user).first()

    if existing_offer:
        return f'A referral offer already exists for {user.username}.'
    else:
        token = str(uuid.uuid4())
        referral_offer = ReferralOffer(referrer=user, token=token)
        referral_offer.save()

    return f'http://127.0.0.1:8000/registration/?ref={user.username}&token={token}'

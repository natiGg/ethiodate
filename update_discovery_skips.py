import re

with open('src/bot/handlers/discovery.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''
@router.callback_query(F.data == "edit_profile")
async def process_edit_profile(callback: CallbackQuery, state: FSMContext):
    # Pre-load data for skipping
    async with async_session_maker() as session:
        user = await session.get(User, callback.from_user.id)
        if user:
            await state.update_data(
                name=user.name,
                age=user.age,
                gender=user.gender,
                gender_preference=user.gender_preference,
                current_country=user.current_country,
                current_city=user.current_city,
                latitude=user.latitude,
                longitude=user.longitude,
                origin_region=user.origin_region,
                willing_to_relocate=user.willing_to_relocate,
                bio=user.bio,
                dob_str=user.date_of_birth,
                lang=user.language_pref
            )

    await callback.message.answer(
        "Let's update your profile! We will start from the beginning. You can press 'Skip' on anything you don't want to change.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
             InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am")]
        ])
    )
    from src.bot.states import Onboarding
    await state.set_state(Onboarding.language)
    await callback.answer()
'''

# Use regex to replace the function
pattern = re.compile(r'@router\.callback_query\(F\.data == "edit_profile"\)\nasync def process_edit_profile.*?await callback\.answer\(\)', re.DOTALL)
new_content = pattern.sub(replacement.strip(), content)

with open('src/bot/handlers/discovery.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

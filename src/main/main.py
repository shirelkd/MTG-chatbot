import logging
import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, \
  CommandHandler, CallbackContext, ConversationHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
GRADE, SCHOOL = range(2)
user_grade = ""
user_school = ""
start_hour_of_activity = {
    "ד": 16,
    "ה": 16,
    "ו": 16,
    "ז": 17,
    "ח": 17,
    "ט": 17,
    "י": 18,
    "יא": 18,
    "יב": 18,
}

async def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
  """Starts the conversation and asks the user about their age."""
  reply_keyboard = [['י״ב', 'י״א', "י", "ט", "ח", "ז", "ו", "ה", "ד"]]

  await update.message.reply_text(
      "Hi! My name is Scout Bot. I will hold a conversation with you. "
      "Send /details to get details about your next activity.\n"
      "Send /cancel to stop talking to me.\n\n"
      "Enter your class grade",
      reply_markup=ReplyKeyboardMarkup(
          reply_keyboard, one_time_keyboard=True,
          input_field_placeholder="Grade"
      ),
  )
  return GRADE


async def cancel(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
  """Cancels and ends the conversation."""
  user = update.message.from_user
  logger.info("User %s canceled the conversation.", user.first_name)
  await update.message.reply_text(
      "Bye! I hope we can talk again some day.",
      reply_markup=ReplyKeyboardRemove()
  )

  return ConversationHandler.END


async def grade(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
  """Stores the selected gender and asks for a photo."""
  user = update.message.from_user
  global user_grade
  user_grade = update.message.text
  logger.info("Grade of %s: %s", user.first_name, update.message.text)
  reply_keyboard = [["ארזים", "שיבולים", "אשלים"]]
  await update.message.reply_text(
      "I see! Please send your school, "
      "so I know which activity you belong to",
      reply_markup=ReplyKeyboardMarkup(
          reply_keyboard, one_time_keyboard=True,
          input_field_placeholder="School"
      ),
  )

  return SCHOOL


async def alarm(context: CallbackContext.DEFAULT_TYPE) -> None:
  """Send the alarm message."""
  job = context.job
  logger.info("job %s", job)
  await context.bot.send_message(job.chat_id, text=f"It's time for Scout "
                                                   f"activity for grade "
                                                   f"{user_grade}! "
                                                   f" Don't forget to wear "
                                                   f"your uniform.")


def remove_job_if_exists(name: str,
    context: CallbackContext.DEFAULT_TYPE) -> bool:
  """Remove job with given name. Returns whether job was removed."""
  current_jobs = context.job_queue.get_jobs_by_name(name)
  if not current_jobs:
    return False
  for job in current_jobs:
    job.schedule_removal()
  return True


async def school(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
  """Stores the school and ends the conversation."""
  user = update.message.from_user
  global user_school
  user_school = update.message.text
  logger.info("School of %s: %s", user.first_name, update.message.text)
  await update.message.reply_text(
      "Thank you!")

  global start_hour_of_activity
  """Add a job to the queue."""
  chat_id = update.effective_message.chat_id
  try:
    job_removed = remove_job_if_exists(str(chat_id), context)
    job_created = context.job_queue.run_daily(alarm,
                                              datetime.time(
                                                  hour=start_hour_of_activity.get(
                                                      user_grade), minute=00,
                                                  tzinfo=pytz.timezone(
                                                      'Asia/Riyadh')),
                                              (1, 4), context=update,
                                              chat_id=chat_id)
    logger.info("next job %s", job_created.next_t)

    text = "Scheduler successfully set!"
    if job_removed:
      text += " Old one was removed."
    await update.effective_message.reply_text(text)

  except (IndexError, ValueError):
    await update.effective_message.reply_text("Wrong number")

  return ConversationHandler.END


async def details(update: Update, context: CallbackContext):
  details_activity = "Hello, " + str(update.message.from_user.first_name) + \
                     ". Your activity for grade " + str(user_grade) + \
                     " is taking place at " + str(user_school) + \
                     " in Tuesday and Friday at " + \
                     str(start_hour_of_activity.get(user_grade)) + ":00 o'clock."
  await context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=details_activity)


if __name__ == '__main__':
  application = ApplicationBuilder().token(
      '5198574730:AAEa2gXkhyohCN7ngzXHJyqmaHDHRmYPoC0').build()

  conv_handler = ConversationHandler(
      entry_points=[CommandHandler("start", start)],
      states={
          GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, grade)],
          SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, school)],
      },
      fallbacks=[],
  )
  details_handler = CommandHandler('details', details)
  cancel_handler = CommandHandler('cancel', cancel)

  application.add_handler(details_handler)
  application.add_handler(conv_handler)
  application.add_handler(cancel_handler)
  application.run_polling()

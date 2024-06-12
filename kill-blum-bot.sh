# Проверка на наличие папки venv
echo "Killing process run-blum-bot.sh ..."
pkill -f run-blum-bot.sh

echo "Deactivatting Python virtual environment"
deactivate

echo "done"
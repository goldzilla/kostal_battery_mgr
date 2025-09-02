# Beispiel: morgens 06:30–08:00 und mittags 10:00–13:30
info, content = set_kostal_state(
    file_path="kostal_battery_state",
    intervals=["06:30-08:00", "10:00-13:30"],
    tz="Europe/Berlin",
    state_in_window="STATE_CHARGING",
    state_default="STATE_NORMAL",
    write_numeric=True,   # auf True setzen, wenn du nur die Zahl schreiben willst
    return_content=True
)

print("Schreib-Info:", info)
print("\nDatei-Inhalt:\n", content)

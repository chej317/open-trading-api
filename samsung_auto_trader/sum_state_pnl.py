import json
from pathlib import Path
p = Path(__file__).resolve().parent / 'trade_state.json'

data = json.loads(p.read_text(encoding='utf-8'))
history = data.get('history', [])

total = sum(entry.get('pnl', 0) for entry in history)
print({"recorded_history_count": len(history), "recorded_total_pnl": total})

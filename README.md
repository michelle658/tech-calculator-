# Tech Calculator

A lightweight desktop calculator built with Python and `tkinter`.

## Features

- Standard and scientific modes
- Dark and light monochrome themes
- Safe math expression evaluation
- Scientific functions like `sqrt`, `sin`, `cos`, `tan`, `log`, `ln`, and `fact`
- Degree and radian angle modes
- Memory controls: `MC`, `MR`, `M+`, `M-`
- Saved calculation history
- Keyboard shortcuts and copy tools

## Requirements

- Python 3
- `tkinter` available in your Python installation

## Run

```powershell
python calculator.py
```

## Keyboard Shortcuts

- `Enter` calculates
- `Backspace` deletes one character
- `Delete` or `Esc` clears the display
- `F1` opens help
- `F2` switches standard/scientific mode
- `F3` toggles theme
- `F4` toggles degree/radian mode
- `Ctrl+C` copies the current result

## Files

- `calculator.py`: main application
- `calculator_history.json`: local history file created when the app runs

## Notes

- The app is desktop-focused because it uses `tkinter`.
- Local history is ignored in Git so personal usage data is not uploaded.

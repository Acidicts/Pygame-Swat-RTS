# Pygame Swat RTS

This is a game in early development, meant to be a SWAT commander experience from a bird's-eye view.

### Features
- Control over other officers
- Radio blocking materials (decrease the chance of an order getting through)
- Weapon characteristics (currently hardcoded; scaffolding for data-driven weapons is in place but not wired up yet)
- Enemy reactions (hide, charge, etc.)
- Team vision cones

### Planned
- Last known enemy position when out of team sight

### Controls
- Left click: select an individual team member
- Left click and drag: select multiple team members
- (Team members selected) Left click on empty ground: move them there
- (Team members selected) Right click: deselect them
- (Team members selected) `X`: toggle shooting (needs radio contact)
- `F3`: toggle AI debug overlay

<img width="795" height="629" alt="Screenshot 2026-10-29 at 11 34 19" src="https://github.com/user-attachments/assets/33320f99-9c04-4674-a8d9-6f7e74ec7191" />


## Installation
Requires Python 3.10+.
1. Clone the repo:
   `git clone https://github.com/Acidicts/Pygame-Swat-RTS && cd Pygame-Swat-RTS`
2. (Recommended) Create and activate a virtual environment:
   `python -m venv .venv`
   then `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
3. Install dependencies:
   `pip install -r requirements.txt`
4. Run the game:
   `python main.py` (use `python3` if `python` isn't found)

"""User-invoked isolated effect-lab launcher; never opens campaign databases."""
from pathlib import Path
import json,shutil,subprocess,tkinter as tk
from tkinter import filedialog,messagebox

def main():
    root=tk.Tk();root.withdraw();folder=Path(__file__).resolve().parents[2]
    game=filedialog.askopenfilename(title='효과 시험장: StarCraft.exe 선택',filetypes=[('StarCraft','StarCraft.exe')])
    if not game:return
    try:
        game=Path(game).resolve()
        if game.name.lower()!='starcraft.exe':raise ValueError('StarCraft.exe를 선택하세요.')
        if game.parent.name.lower()=='x86':raise ValueError('x86_64 폴더의 StarCraft.exe를 선택하세요.')
        game_root=game.parent.parent if game.parent.name.lower() in ('x86','x86_64') else game.parent
        native=folder/'sc1/native_campaign';pointer=json.loads((native/'current_build.json').read_text(encoding='utf8'))
        release=(native/pointer['manifest']).resolve().parent
        source=folder/'sc1/effect_lab/SC1_Effect_Lab.scx'
        destination=game_root/'Maps/SC1_Roguelike/SC1_Effect_Lab.scx';destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists() and destination.read_bytes()!=source.read_bytes():
            backup=destination.with_suffix('.scx.before-effect-lab')
            if backup.exists():raise ValueError('시험 지도 백업이 이미 있습니다. 기존 백업을 확인하세요.')
            shutil.copy2(destination,backup)
        shutil.copy2(source,destination)
        subprocess.Popen([str(release/'samase64.exe'),str(release/'overlay'),'--starcraft-exe',str(game),'--log','--no-debug'],cwd=release,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        messagebox.showinfo('효과 통합 시험장','싱글 플레이 → 사용자 지정 게임 → SC1_Roguelike/SC1_Effect_Lab.scx → 유즈맵 설정으로 시작하세요.\n\n채팅 -help, 효과 목록은 Effect_Checklist.html입니다. 캠페인 기록 연결은 필요 없습니다.')
    except Exception as error:messagebox.showerror('시험장 실행 오류',str(error))
    finally:root.destroy()

if __name__=='__main__':main()

import math
import statistics
import tkinter as tk
from tkinter import ttk, messagebox


def normal_cdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.0
    z = (x - mu) / (sigma * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))


def parse_data(raw: str) -> list[float]:
    cleaned = raw.replace(',', ' ').replace(';', ' ')
    parts = [p for p in cleaned.split() if p]
    if len(parts) < 2:
        raise ValueError('데이터는 최소 2개 이상 필요합니다.')
    try:
        return [float(p) for p in parts]
    except ValueError as exc:
        raise ValueError('데이터에 숫자가 아닌 값이 포함되어 있습니다.') from exc


def calc_capability(values: list[float], lsl: float, usl: float, target: float | None = None) -> dict:
    if lsl >= usl:
        raise ValueError('LSL은 USL보다 작아야 합니다.')

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    if stdev <= 0:
        raise ValueError('표준편차가 0입니다. 데이터 변동이 있어야 분석 가능합니다.')

    cp = (usl - lsl) / (6 * stdev)
    cpu = (usl - mean) / (3 * stdev)
    cpl = (mean - lsl) / (3 * stdev)
    cpk = min(cpu, cpl)

    if target is None:
        target = (lsl + usl) / 2
    k = abs(mean - target) / ((usl - lsl) / 2)

    p_low = normal_cdf(lsl, mean, stdev)
    p_high = 1 - normal_cdf(usl, mean, stdev)
    ppm = (p_low + p_high) * 1_000_000

    if cpk >= 1.67:
        grade = '매우 우수 (Cpk ≥ 1.67)'
    elif cpk >= 1.33:
        grade = '양호 (Cpk ≥ 1.33)'
    elif cpk >= 1.0:
        grade = '개선 필요 (1.0 ≤ Cpk < 1.33)'
    else:
        grade = '불량 위험 높음 (Cpk < 1.0)'

    return {
        'count': len(values),
        'mean': mean,
        'stdev': stdev,
        'lsl': lsl,
        'usl': usl,
        'cp': cp,
        'cpu': cpu,
        'cpl': cpl,
        'cpk': cpk,
        'k': k,
        'ppm': ppm,
        'grade': grade,
    }


class CapabilityApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('공정능력 분석기 (Tkinter)')
        self.geometry('820x620')

        self._build_ui()

    def _build_ui(self) -> None:
        frm_top = ttk.Frame(self, padding=10)
        frm_top.pack(fill=tk.X)

        ttk.Label(frm_top, text='LSL').grid(row=0, column=0, sticky='w')
        self.ent_lsl = ttk.Entry(frm_top, width=14)
        self.ent_lsl.grid(row=0, column=1, padx=5)

        ttk.Label(frm_top, text='USL').grid(row=0, column=2, sticky='w')
        self.ent_usl = ttk.Entry(frm_top, width=14)
        self.ent_usl.grid(row=0, column=3, padx=5)

        ttk.Label(frm_top, text='Target(선택)').grid(row=0, column=4, sticky='w')
        self.ent_target = ttk.Entry(frm_top, width=14)
        self.ent_target.grid(row=0, column=5, padx=5)

        ttk.Button(frm_top, text='분석 실행', command=self.analyze).grid(row=0, column=6, padx=8)
        ttk.Button(frm_top, text='샘플 데이터', command=self.fill_sample).grid(row=0, column=7, padx=5)

        frm_data = ttk.LabelFrame(self, text='측정 데이터 입력 (공백/쉼표/줄바꿈 구분)', padding=10)
        frm_data.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.txt_data = tk.Text(frm_data, height=14)
        self.txt_data.pack(fill=tk.BOTH, expand=True)

        frm_result = ttk.LabelFrame(self, text='분석 결과', padding=10)
        frm_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.txt_result = tk.Text(frm_result, height=16, state='disabled')
        self.txt_result.pack(fill=tk.BOTH, expand=True)

        hint = (
            '판정 기준 예시: Cpk≥1.33 권장, Cpk≥1.67 매우 우수\n'
            '※ 본 도구는 정규분포 가정 기반의 기본 공정능력 계산기입니다.'
        )
        ttk.Label(self, text=hint, foreground='#444').pack(anchor='w', padx=12, pady=(0, 8))

    def fill_sample(self) -> None:
        sample = [
            9.97, 10.01, 10.04, 10.02, 9.99, 10.00, 9.98, 10.03, 10.01, 9.96,
            10.05, 10.00, 10.02, 9.99, 10.01, 10.04, 9.97, 10.00, 10.02, 9.98,
        ]
        self.ent_lsl.delete(0, tk.END)
        self.ent_lsl.insert(0, '9.8')
        self.ent_usl.delete(0, tk.END)
        self.ent_usl.insert(0, '10.2')
        self.ent_target.delete(0, tk.END)
        self.ent_target.insert(0, '10.0')

        self.txt_data.delete('1.0', tk.END)
        self.txt_data.insert(tk.END, '\n'.join(str(v) for v in sample))

    def analyze(self) -> None:
        try:
            lsl = float(self.ent_lsl.get().strip())
            usl = float(self.ent_usl.get().strip())
            target_raw = self.ent_target.get().strip()
            target = float(target_raw) if target_raw else None

            values = parse_data(self.txt_data.get('1.0', tk.END))
            result = calc_capability(values, lsl, usl, target)
            self._render_result(result)
        except Exception as exc:  # UI용 예외 표시
            messagebox.showerror('입력 오류', str(exc))

    def _render_result(self, r: dict) -> None:
        output = (
            f"데이터 수(n): {r['count']}\n"
            f"평균(Mean): {r['mean']:.6f}\n"
            f"표준편차(Stdev): {r['stdev']:.6f}\n"
            f"LSL / USL: {r['lsl']:.6f} / {r['usl']:.6f}\n"
            f"\n"
            f"Cp  : {r['cp']:.4f}\n"
            f"CPU : {r['cpu']:.4f}\n"
            f"CPL : {r['cpl']:.4f}\n"
            f"Cpk : {r['cpk']:.4f}\n"
            f"k(중심이탈도): {r['k']:.4f}\n"
            f"예상 불량률(PPM): {r['ppm']:.2f}\n"
            f"\n"
            f"종합 판정: {r['grade']}\n"
        )

        self.txt_result.config(state='normal')
        self.txt_result.delete('1.0', tk.END)
        self.txt_result.insert(tk.END, output)
        self.txt_result.config(state='disabled')


if __name__ == '__main__':
    app = CapabilityApp()
    app.mainloop()

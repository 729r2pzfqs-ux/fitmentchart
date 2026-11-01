import subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
S = os.path.dirname(os.path.abspath(__file__)); C = sys.argv[1]
jobs = [(y, mk, md) for y in range(2005, 2027) for mk, md in
        (("Toyota", "Tacoma"), ("Ford", "F-150"), ("Honda", "Civic"), ("Chevrolet", "Silverado 1500"), ("Jeep", "Wrangler"),
         ("Toyota", "Camry"), ("Toyota", "Corolla"), ("Honda", "Accord"), ("Ram", "1500"), ("Dodge", "Ram 1500"), ("Tesla", "Model 3"))]
def run(j):
    y, mk, md = j
    f = os.path.join(C, f"{y}_{mk}_{md.replace(' ', '_')}.json")
    if os.path.exists(f) and os.path.getsize(f) > 0:
        return
    r = subprocess.run([sys.executable, "-I", os.path.join(S, "rxall.py"), str(y), mk, md, f], capture_output=True, text=True)
    if r.returncode: print("FAIL", j, r.stderr[-200:])
with ThreadPoolExecutor(3) as ex:
    list(ex.map(run, jobs))
print(len(os.listdir(C)), "files")

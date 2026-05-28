import sounddevice as sd
import numpy as np

print("Available devices:")
print(sd.query_devices())
print()
print("Default input:", sd.query_devices(kind='input')['name'])
print()
print("Speak for 5 seconds...")
recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()
rms = float(np.sqrt(np.mean(recording**2)))
max_val = float(np.max(np.abs(recording)))
print(f"RMS volume:  {rms:.6f}")
print(f"Max volume:  {max_val:.6f}")
if rms < 0.001:
    print("MIC TOO QUIET — wrong device or mic not picking up")
elif rms > 0.01:
    print("Mic level GOOD")
else:
    print("Mic level LOW — threshold needs adjusting")
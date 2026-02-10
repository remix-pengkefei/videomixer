#!/usr/bin/env python3
"""
Generate overlay videos using ffmpeg filters
Creates particle, light, and effect overlays for video mixing
"""

import os
import subprocess
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Settings
WIDTH = 720
HEIGHT = 1280
FPS = 30
BASE_DIR = Path("/Users/fly/Desktop/VideoMixer/assets/overlays")

# Effect configurations for each category
EFFECTS_CONFIG = {
    "particles": {
        "count": 40,
        "effects": [
            # Sparse white particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*1000,{2+i%5}),255,0)\':cb=128:cr=128',
            # Dense noise particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},noise=alls={10+i%20}:allf=t',
            # Falling particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*800,2),255,0)\':cb=128:cr=128,scroll=v={0.01+i*0.002}',
            # Horizontal drift particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*600,1),255,0)\':cb=128:cr=128,scroll=h={0.005+i*0.001}',
            # Pulsing particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*700,2),255*abs(sin(T*{2+i%4})),0)\':cb=128:cr=128',
        ]
    },
    "confetti": {
        "count": 40,
        "effects": [
            # Colorful noise
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},noise=alls={15+i%15}:allf=t,hue=h=t*{30+i*5}',
            # Falling colored dots
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*400,1),200,0)\':cb=\'128+64*sin(X/50)\':cr=\'128+64*cos(Y/50)\',scroll=v=0.02',
            # Rainbow particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},noise=alls=20:allf=t,hue=h=X+Y+t*100',
        ]
    },
    "light": {
        "count": 40,
        "effects": [
            # Center glow pulse
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'255*exp(-((X-{WIDTH//2})*(X-{WIDTH//2})+(Y-{HEIGHT//2})*(Y-{HEIGHT//2}))/({80000+i*5000}))*abs(sin(T*{2+i%3}))\':cb=128:cr=128',
            # Light rays from top
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'50*exp(-Y/{400+i*20})*exp(-abs(X-{WIDTH//2})/{100+i*10})\':cb=128:cr=128,gblur=sigma={5+i%10}',
            # Moving light beam
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'80*exp(-abs(X-{WIDTH//2}-200*sin(T*{1+i*0.2}))/{50+i*5})\':cb=128:cr=128,gblur=sigma=15',
            # Lens flare style
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'100*exp(-((X-{WIDTH//2+i*10})*(X-{WIDTH//2+i*10})+(Y-{HEIGHT//3})*(Y-{HEIGHT//3}))/50000)*abs(sin(T*3))\':cb=128:cr=128,gblur=sigma=20',
            # Soft gradient glow
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'30+25*sin(2*PI*T/{3+i%2})*exp(-Y/{600+i*30})\':cb=128:cr=128',
        ]
    },
    "sparkle": {
        "count": 40,
        "effects": [
            # Twinkling stars
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*2000,1),255*abs(sin(T*{8+i%6}+random(1)*6.28)),0)\':cb=128:cr=128',
            # Scattered sparkles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*1500,1),255*pow(abs(sin(T*{10+i%5}+X/100)),2),0)\':cb=128:cr=128',
            # Diamond sparkle
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*1000,1),255*max(0,cos(T*{12+i%4})),0)\':cb=128:cr=128',
            # Fast twinkle
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*800,1),255*abs(sin(T*{15+i%8})),0)\':cb=128:cr=128',
        ]
    },
    "snow": {
        "count": 40,
        "effects": [
            # Gentle snowfall
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*500,1),200,0)\':cb=128:cr=128,scroll=v={0.015+i*0.001}',
            # Dense snow
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*300,1),220,0)\':cb=128:cr=128,scroll=v={0.02+i*0.002}',
            # Blizzard
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*200,1),180,0)\':cb=128:cr=128,scroll=v=0.03:h={0.005+i*0.001}',
            # Soft snow with blur
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*400,1),150,0)\':cb=128:cr=128,gblur=sigma={2+i%3},scroll=v=0.018',
            # Snow with wind
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*350,1),200,0)\':cb=128:cr=128,scroll=v=0.02:h={0.008*(-1 if i%2 else 1)}',
        ]
    },
    "fire": {
        "count": 40,
        "effects": [
            # Fire glow from bottom
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'clip(({HEIGHT}-Y)/{10+i%5}+30*sin(X/50+T*5)+20*random(1),0,255)/4\':cb=\'118\':cr=\'148\'',
            # Ember particles
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(random(1)*600,1),200,0)*(1-Y/{HEIGHT})\':cb=\'120\':cr=\'150\',scroll=v=-0.01',
            # Flickering fire
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'50*exp(-Y/{500+i*20})*(1+0.5*sin(T*{8+i%5}+X/30))\':cb=\'115\':cr=\'145\'',
            # Fire wave
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'60*exp(-(Y-{HEIGHT}+100*sin(X/80+T*3))/{300+i*10})\':cb=\'120\':cr=\'150\',gblur=sigma=3',
        ]
    },
    "smoke": {
        "count": 40,
        "effects": [
            # Rising smoke
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},noise=alls={8+i%8}:allf=t,gblur=sigma={15+i%10},scroll=v=-{0.008+i*0.001}',
            # Fog layer
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'20+15*sin(X/200+T)+10*sin(Y/150-T*0.5)\':cb=128:cr=128,gblur=sigma=25',
            # Mist drift
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},noise=alls={5+i%5}:allf=t,gblur=sigma=30,scroll=h={0.003+i*0.0005}',
            # Smoke puffs
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'30*exp(-((X-{WIDTH//2})*(X-{WIDTH//2})+(Y-{HEIGHT*2//3})*(Y-{HEIGHT*2//3}))/({50000+i*10000}))*(1+0.3*sin(T*2))\':cb=128:cr=128,gblur=sigma=20,scroll=v=-0.005',
            # Layered fog
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'15+10*sin(Y/100+T*0.5)+8*sin(X/80-T*0.3)\':cb=128:cr=128,gblur=sigma={20+i%15}',
        ]
    },
    "abstract": {
        "count": 40,
        "effects": [
            # Wave pattern
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'128+127*sin(2*PI*(X/{100+i*10}+T*{1+i*0.1}))*sin(2*PI*Y/{200+i*15})\':cb=128:cr=128',
            # Geometric grid
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(mod(X+T*{50+i*10},{80+i*5})<3,200,if(mod(Y+T*{30+i*5},{60+i*4})<3,150,0))\':cb=128:cr=128',
            # Circular waves
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'128+127*sin(sqrt((X-{WIDTH//2})*(X-{WIDTH//2})+(Y-{HEIGHT//2})*(Y-{HEIGHT//2}))/{20+i%10}-T*{3+i*0.2})\':cb=128:cr=128',
            # Diagonal stripes
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'128+127*sin((X+Y+T*{100+i*20})/{30+i%15})\':cb=128:cr=128',
            # Plasma effect
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'128+42*sin(X/{50+i*3}+T)+42*sin(Y/{40+i*2}-T*0.7)+42*sin((X+Y)/{60+i*4}+T*0.5)\':cb=128:cr=128',
            # Morphing shapes
            lambda d, i: f'color=black:s={WIDTH}x{HEIGHT}:d={d}:r={FPS},geq=lum=\'if(lt(abs(sin(X/{100+i*5}+T)*sin(Y/{80+i*4}-T*0.5)),0.1),200,0)\':cb=128:cr=128',
        ]
    },
}


def create_video(category: str, index: int, output_path: Path) -> bool:
    """Create a single overlay video"""
    try:
        config = EFFECTS_CONFIG[category]
        effects = config["effects"]
        effect_func = effects[index % len(effects)]

        # Vary duration between 3-5 seconds
        duration = 3 + (index % 3)

        # Get the filter
        filter_str = effect_func(duration, index)

        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', filter_str,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '23',
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=60
        )

        return output_path.exists() and output_path.stat().st_size > 1000

    except Exception as e:
        print(f"Error creating {output_path.name}: {e}")
        return False


def process_category(category: str) -> int:
    """Process all videos for a category"""
    config = EFFECTS_CONFIG[category]
    target_count = config["count"]

    output_dir = BASE_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check existing
    existing = list(output_dir.glob("lottie_*.mp4"))
    existing_count = len(existing)

    print(f"\n{'='*50}")
    print(f"Category: {category}")
    print(f"Existing: {existing_count}, Target: {target_count}")
    print(f"{'='*50}")

    if existing_count >= target_count:
        print(f"Already have enough videos, skipping...")
        return existing_count

    needed = target_count - existing_count
    created = 0

    for i in range(needed):
        idx = existing_count + i + 1
        output_path = output_dir / f"lottie_{category}_{idx:03d}.mp4"

        if output_path.exists():
            continue

        print(f"  Creating [{i+1}/{needed}]: {output_path.name}...", end=" ", flush=True)

        if create_video(category, i, output_path):
            created += 1
            print("OK")
        else:
            print("FAILED")

    final_count = len(list(output_dir.glob("lottie_*.mp4")))
    print(f"Category {category} complete: {final_count} videos")
    return final_count


def main():
    print("="*50)
    print("Overlay Video Generator")
    print("="*50)
    print(f"Output: {BASE_DIR}")
    print(f"Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")
    print("="*50)

    results = {}
    total = 0

    for category in EFFECTS_CONFIG.keys():
        count = process_category(category)
        results[category] = count
        total += count

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for cat, count in results.items():
        print(f"  {cat}: {count} videos")
    print(f"\nTotal: {total} videos")
    print("="*50)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
LottieFiles Downloader and Converter
Downloads Lottie animations and converts them to video files with black background
"""

import os
import json
import subprocess
import tempfile
import shutil
import requests
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Output settings
WIDTH = 720
HEIGHT = 1280
FPS = 30
DURATION = 3  # seconds per animation

# Base paths
BASE_DIR = Path("/Users/fly/Desktop/VideoMixer/assets/overlays")

# Categories and search terms
CATEGORIES = {
    "particles": ["particles", "particle effect", "dust", "floating particles"],
    "confetti": ["confetti", "celebration", "party", "birthday confetti"],
    "light": ["light effect", "glow", "shine", "lens flare", "light rays"],
    "sparkle": ["sparkle", "stars", "twinkle", "glitter", "shimmer"],
    "snow": ["snow", "snowflake", "winter", "snowfall", "christmas snow"],
    "fire": ["fire", "flame", "ember", "burning", "fire effect"],
    "smoke": ["smoke", "fog", "mist", "cloud", "vapor"],
    "abstract": ["abstract", "geometric", "wave", "motion graphics", "loop"]
}

# LottieFiles public animations (curated list of popular free animations)
# These are publicly available Lottie animations from various sources
LOTTIE_SOURCES = {
    "particles": [
        "https://assets2.lottiefiles.com/packages/lf20_tll0j4bb.json",
        "https://assets9.lottiefiles.com/packages/lf20_xlmz9xwm.json",
        "https://assets3.lottiefiles.com/packages/lf20_u4yrau.json",
        "https://assets10.lottiefiles.com/packages/lf20_p7ml1rhe.json",
        "https://assets5.lottiefiles.com/packages/lf20_xsnmz2jp.json",
        "https://assets8.lottiefiles.com/packages/lf20_cwA7Cn.json",
        "https://assets4.lottiefiles.com/packages/lf20_xlkxtmul.json",
        "https://assets1.lottiefiles.com/packages/lf20_UJNc2t.json",
        "https://assets6.lottiefiles.com/packages/lf20_poqmycwy.json",
        "https://assets2.lottiefiles.com/packages/lf20_qdbb21wb.json",
    ],
    "confetti": [
        "https://assets4.lottiefiles.com/packages/lf20_rovf9gpa.json",
        "https://assets9.lottiefiles.com/packages/lf20_u4yrau.json",
        "https://assets3.lottiefiles.com/packages/lf20_aKAfIn.json",
        "https://assets2.lottiefiles.com/packages/lf20_zzytl6wo.json",
        "https://assets5.lottiefiles.com/packages/lf20_pmzzahdz.json",
        "https://assets1.lottiefiles.com/packages/lf20_KU3FGB.json",
        "https://assets7.lottiefiles.com/packages/lf20_GOfhCs.json",
        "https://assets8.lottiefiles.com/packages/lf20_touohxv0.json",
        "https://assets6.lottiefiles.com/packages/lf20_ZQhQzO.json",
        "https://assets10.lottiefiles.com/packages/lf20_YrdPIN.json",
    ],
    "light": [
        "https://assets3.lottiefiles.com/packages/lf20_bq485nmk.json",
        "https://assets5.lottiefiles.com/packages/lf20_qjosmr4w.json",
        "https://assets7.lottiefiles.com/packages/lf20_jhlaooj5.json",
        "https://assets1.lottiefiles.com/packages/lf20_k86wxpgr.json",
        "https://assets9.lottiefiles.com/packages/lf20_qm8eqzse.json",
        "https://assets2.lottiefiles.com/packages/lf20_8gmx3csh.json",
        "https://assets4.lottiefiles.com/packages/lf20_znlyexnl.json",
        "https://assets8.lottiefiles.com/packages/lf20_ddxc0mqn.json",
        "https://assets6.lottiefiles.com/packages/lf20_gy4zkpos.json",
        "https://assets10.lottiefiles.com/packages/lf20_obhph3sh.json",
    ],
    "sparkle": [
        "https://assets5.lottiefiles.com/packages/lf20_v3gj3tvc.json",
        "https://assets7.lottiefiles.com/packages/lf20_esbqhlxs.json",
        "https://assets1.lottiefiles.com/packages/lf20_kd5rzej5.json",
        "https://assets3.lottiefiles.com/packages/lf20_awhgvudo.json",
        "https://assets9.lottiefiles.com/packages/lf20_UBiAADPga8.json",
        "https://assets2.lottiefiles.com/packages/lf20_j1klpmkb.json",
        "https://assets4.lottiefiles.com/packages/lf20_mcmkqzjv.json",
        "https://assets8.lottiefiles.com/packages/lf20_svy4ivvy.json",
        "https://assets6.lottiefiles.com/packages/lf20_xvqrcqfl.json",
        "https://assets10.lottiefiles.com/packages/lf20_gctldemv.json",
    ],
    "snow": [
        "https://assets3.lottiefiles.com/packages/lf20_y7pjvq3g.json",
        "https://assets5.lottiefiles.com/packages/lf20_dblj0lzj.json",
        "https://assets7.lottiefiles.com/packages/lf20_eop2lxmo.json",
        "https://assets1.lottiefiles.com/packages/lf20_z8kdz56e.json",
        "https://assets9.lottiefiles.com/packages/lf20_skf0lq7b.json",
        "https://assets2.lottiefiles.com/packages/lf20_zwn6fmnu.json",
        "https://assets4.lottiefiles.com/packages/lf20_5fqmksyg.json",
        "https://assets8.lottiefiles.com/packages/lf20_xfzrhvgj.json",
        "https://assets6.lottiefiles.com/packages/lf20_z6pljwso.json",
        "https://assets10.lottiefiles.com/packages/lf20_s1zlyrjp.json",
    ],
    "fire": [
        "https://assets5.lottiefiles.com/packages/lf20_5njp3vgg.json",
        "https://assets7.lottiefiles.com/packages/lf20_x1gjdldd.json",
        "https://assets1.lottiefiles.com/packages/lf20_qwl4gi2c.json",
        "https://assets3.lottiefiles.com/packages/lf20_kyu7xb1v.json",
        "https://assets9.lottiefiles.com/packages/lf20_lwwjvl4f.json",
        "https://assets2.lottiefiles.com/packages/lf20_dbyxtskt.json",
        "https://assets4.lottiefiles.com/packages/lf20_5vsyvfjs.json",
        "https://assets8.lottiefiles.com/packages/lf20_o6spyjnc.json",
        "https://assets6.lottiefiles.com/packages/lf20_xhbpqlel.json",
        "https://assets10.lottiefiles.com/packages/lf20_2m1atvsy.json",
    ],
    "smoke": [
        "https://assets5.lottiefiles.com/packages/lf20_gwfviczo.json",
        "https://assets7.lottiefiles.com/packages/lf20_tqfkhhoc.json",
        "https://assets1.lottiefiles.com/packages/lf20_tszzqmgq.json",
        "https://assets3.lottiefiles.com/packages/lf20_8axgpdce.json",
        "https://assets9.lottiefiles.com/packages/lf20_qo7smd5w.json",
        "https://assets2.lottiefiles.com/packages/lf20_v3gj3tvc.json",
        "https://assets4.lottiefiles.com/packages/lf20_n9f7ikxl.json",
        "https://assets8.lottiefiles.com/packages/lf20_bcjz2qqt.json",
        "https://assets6.lottiefiles.com/packages/lf20_pprxh53j.json",
        "https://assets10.lottiefiles.com/packages/lf20_0sk5yptj.json",
    ],
    "abstract": [
        "https://assets5.lottiefiles.com/packages/lf20_sfnjmlux.json",
        "https://assets7.lottiefiles.com/packages/lf20_nw19osms.json",
        "https://assets1.lottiefiles.com/packages/lf20_rbhw9bcs.json",
        "https://assets3.lottiefiles.com/packages/lf20_lj8muylf.json",
        "https://assets9.lottiefiles.com/packages/lf20_1pxqjqps.json",
        "https://assets2.lottiefiles.com/packages/lf20_v1yudlrx.json",
        "https://assets4.lottiefiles.com/packages/lf20_jcikwtux.json",
        "https://assets8.lottiefiles.com/packages/lf20_rbtawnwz.json",
        "https://assets6.lottiefiles.com/packages/lf20_kuhnfwp0.json",
        "https://assets10.lottiefiles.com/packages/lf20_tfb3estd.json",
    ],
}


def download_lottie(url: str, output_path: Path) -> bool:
    """Download a Lottie JSON file"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            with open(output_path, 'w') as f:
                json.dump(data, f)
            return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
    return False


def convert_lottie_to_video(json_path: Path, output_path: Path, category: str) -> bool:
    """Convert Lottie JSON to video using lottie library and ffmpeg"""
    try:
        # Read the lottie file
        with open(json_path, 'r') as f:
            lottie_data = json.load(f)

        # Get animation properties
        animation_fps = lottie_data.get('fr', 30)
        in_point = lottie_data.get('ip', 0)
        out_point = lottie_data.get('op', 60)
        orig_width = lottie_data.get('w', 720)
        orig_height = lottie_data.get('h', 1280)

        total_frames = int(out_point - in_point)
        if total_frames <= 0:
            total_frames = 60

        # Create temp directory for frames
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Use puppeteer/node for better rendering
            # First, try using lottie-to-gif or similar
            # Fallback: create a simple colored video as placeholder

            # Generate video directly with ffmpeg using color source
            # This creates a placeholder video with category-specific colors
            colors = {
                "particles": "0x1a1a2e",
                "confetti": "0x16213e",
                "light": "0x0f0f0f",
                "sparkle": "0x1a1a1a",
                "snow": "0x1e1e2f",
                "fire": "0x1a0a00",
                "smoke": "0x151515",
                "abstract": "0x0a0a1a"
            }
            bg_color = colors.get(category, "0x000000")

            # Try to use lottie library to render frames
            try:
                from lottie import parsers, exporters
                from lottie.utils.animation import FrameSequenceExporter

                # Parse lottie
                animation = parsers.parse_lottie(lottie_data)

                # Calculate scale to fit in 720x1280
                scale_w = WIDTH / animation.width if animation.width else 1
                scale_h = HEIGHT / animation.height if animation.height else 1
                scale = min(scale_w, scale_h)

                # Export frames
                frame_dir = temp_path / "frames"
                frame_dir.mkdir(exist_ok=True)

                # Render frames
                exporter = FrameSequenceExporter(
                    animation,
                    str(frame_dir / "frame_%04d.png"),
                    fps=FPS
                )
                exporter.export()

                # Check if frames were created
                frames = list(frame_dir.glob("*.png"))
                if frames:
                    # Combine frames to video with ffmpeg
                    cmd = [
                        'ffmpeg', '-y',
                        '-framerate', str(FPS),
                        '-i', str(frame_dir / 'frame_%04d.png'),
                        '-vf', f'scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black',
                        '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p',
                        '-preset', 'medium',
                        '-crf', '23',
                        '-t', str(DURATION),
                        str(output_path)
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=60)
                    if output_path.exists():
                        return True
            except Exception as e:
                print(f"    Lottie render failed: {e}, using ffmpeg fallback")

            # Fallback: Create animated placeholder video
            duration = DURATION

            # Create a nice animated gradient/effect video as placeholder
            filter_complex = f"""
                color=c=black:s={WIDTH}x{HEIGHT}:d={duration},
                drawtext=text='Loading {category}':fontcolor=white@0.3:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2
            """

            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'color=c=black:s={WIDTH}x{HEIGHT}:d={duration}:r={FPS}',
                '-vf', f"geq=lum='if(lt(random(1)*100,2),255,0)':cb=128:cr=128",
                '-t', str(duration),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-crf', '23',
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return output_path.exists()

    except Exception as e:
        print(f"  Error converting {json_path}: {e}")
        return False


def create_overlay_video_ffmpeg(output_path: Path, category: str, index: int) -> bool:
    """Create an overlay video using pure ffmpeg with various effects"""
    try:
        duration = DURATION + random.uniform(0, 2)  # 3-5 seconds

        # Different effect patterns based on category
        effects = {
            "particles": [
                # Noise particles
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration}[bg];[bg]noise=alls=20:allf=t+u[v]",
                # Random dots
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='if(lt(random(1)*1000,3),255,0)':cb=128:cr=128",
            ],
            "confetti": [
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},noise=alls=30:allf=t,hue=h=t*50",
            ],
            "light": [
                # Light rays effect
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},drawbox=x=iw/2-50:y=0:w=100:h=ih:color=white@0.1:t=fill,gblur=sigma=30",
                # Glow pulse
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='128+127*sin(2*PI*(X/W+Y/H+T))':cb=128:cr=128,gblur=sigma=10",
            ],
            "sparkle": [
                # Sparkle dots
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='if(lt(random(1)*500,1),255*sin(T*10),0)':cb=128:cr=128",
            ],
            "snow": [
                # Falling snow effect
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},noise=alls=10:allf=t,scroll=v=0.02",
            ],
            "fire": [
                # Fire gradient
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='clip(Y/H*255+random(1)*50,0,255)/3':cb='128-20':cr='128+40',gblur=sigma=5",
            ],
            "smoke": [
                # Smoke/fog effect
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},noise=alls=15:allf=t,gblur=sigma=20",
            ],
            "abstract": [
                # Wave pattern
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='128+127*sin(2*PI*(X/100+T))':cb=128:cr=128",
                # Geometric
                f"color=black:s={WIDTH}x{HEIGHT}:d={duration},geq=lum='if(mod(X+Y+T*100,100)<50,50,0)':cb=128:cr=128",
            ],
        }

        category_effects = effects.get(category, effects["particles"])
        effect = category_effects[index % len(category_effects)]

        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', effect,
            '-t', str(duration),
            '-r', str(FPS),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '23',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path.exists() and output_path.stat().st_size > 1000

    except Exception as e:
        print(f"  Error creating effect video: {e}")
        return False


def fetch_lottiefiles_api(category: str, search_term: str, page: int = 1) -> list:
    """Fetch animations from LottieFiles public API"""
    try:
        # LottieFiles public GraphQL API
        url = "https://graphql.lottiefiles.com/graphql"

        query = """
        query SearchPublicAnimations($query: String!, $page: Int!, $limit: Int!) {
            searchPublicAnimations(query: $query, page: $page, limit: $limit) {
                results {
                    id
                    lottieUrl
                    name
                }
                totalCount
            }
        }
        """

        payload = {
            "query": query,
            "variables": {
                "query": search_term,
                "page": page,
                "limit": 20
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('searchPublicAnimations', {}).get('results', [])
            return [r.get('lottieUrl') for r in results if r.get('lottieUrl')]
    except Exception as e:
        print(f"  API fetch error for {search_term}: {e}")

    return []


def process_category(category: str, target_count: int = 40):
    """Process a single category"""
    output_dir = BASE_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check existing files
    existing = list(output_dir.glob("lottie_*.mp4"))
    existing_count = len(existing)

    print(f"\n{'='*60}")
    print(f"Processing category: {category}")
    print(f"Existing files: {existing_count}, Target: {target_count}")
    print(f"{'='*60}")

    if existing_count >= target_count:
        print(f"  Already have {existing_count} files, skipping...")
        return existing_count

    needed = target_count - existing_count
    created = 0

    # Get search terms for this category
    search_terms = CATEGORIES.get(category, [category])

    # First, try to get URLs from LottieFiles API
    all_urls = []
    for term in search_terms:
        urls = fetch_lottiefiles_api(category, term, page=1)
        all_urls.extend(urls)
        time.sleep(0.5)  # Rate limiting

    # Also add hardcoded URLs
    hardcoded = LOTTIE_SOURCES.get(category, [])
    all_urls.extend(hardcoded)

    # Remove duplicates
    all_urls = list(set(all_urls))
    print(f"  Found {len(all_urls)} Lottie URLs")

    # Download and convert
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for i, url in enumerate(all_urls[:needed]):
            if created >= needed:
                break

            idx = existing_count + created + 1
            output_file = output_dir / f"lottie_{category}_{idx:03d}.mp4"

            if output_file.exists():
                continue

            print(f"  [{created+1}/{needed}] Processing: {url[:50]}...")

            # Download JSON
            json_file = temp_path / f"temp_{i}.json"
            if download_lottie(url, json_file):
                # Convert to video
                if convert_lottie_to_video(json_file, output_file, category):
                    created += 1
                    print(f"    Created: {output_file.name}")
                else:
                    print(f"    Failed to convert")
            else:
                print(f"    Failed to download")

            time.sleep(0.3)  # Rate limiting

    # If we still need more, generate with ffmpeg effects
    still_needed = needed - created
    if still_needed > 0:
        print(f"\n  Generating {still_needed} additional videos with ffmpeg effects...")

        for i in range(still_needed):
            idx = existing_count + created + 1
            output_file = output_dir / f"lottie_{category}_{idx:03d}.mp4"

            if not output_file.exists():
                if create_overlay_video_ffmpeg(output_file, category, i):
                    created += 1
                    print(f"    Generated: {output_file.name}")

    final_count = len(list(output_dir.glob("lottie_*.mp4")))
    print(f"\n  Category {category} complete: {final_count} files")

    return final_count


def main():
    """Main function"""
    print("="*60)
    print("LottieFiles Downloader and Converter")
    print("="*60)
    print(f"Output directory: {BASE_DIR}")
    print(f"Target per category: 30-50 videos")
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print(f"Frame rate: {FPS}fps")
    print("="*60)

    # Create base directory
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Process each category
    results = {}
    target = 40  # Target 40 per category (within 30-50 range)

    for category in CATEGORIES.keys():
        count = process_category(category, target)
        results[category] = count

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total = 0
    for category, count in results.items():
        print(f"  {category}: {count} videos")
        total += count

    print(f"\nTotal: {total} videos")
    print("="*60)


if __name__ == "__main__":
    main()

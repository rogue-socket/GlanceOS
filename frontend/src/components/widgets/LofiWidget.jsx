import { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import WidgetCard from '../WidgetCard';

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function normalizeFrame(frame) {
  if (!frame) return '';

  const lines = frame.replace(/\r/g, '').split('\n');
  while (lines.length > 0 && lines[0].trim() === '') lines.shift();
  while (lines.length > 0 && lines[lines.length - 1].trim() === '') lines.pop();

  let minIndent = Infinity;
  for (const line of lines) {
    if (!line.trim()) continue;
    const indent = line.match(/^\s*/)?.[0]?.length || 0;
    if (indent < minIndent) minIndent = indent;
  }

  if (Number.isFinite(minIndent) && minIndent > 0) {
    return lines.map(line => line.slice(Math.min(minIndent, line.length))).join('\n');
  }

  return lines.join('\n');
}

const SPINNING_DONUT_FRAMES = [
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
        *
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \   *
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'  *
      '-...-'
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
 * /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
`,
  String.raw`
      .-"""-.
  * .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |  *
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
  *   '-...-'
`,
  String.raw`
      .-"""-.
    .'  .-.  '.
   /  .'   '.  \
  |  |  (_)  |  |
   \  '.   .'  /
    '.  '-'  .'
      '-...-'
`,
];

const LOCAL_SCENES = [
  {
    art: String.raw`
      _._     _,-'""-._
     (,-._,'(       |\'-/|
         -.-' \ )-'( , o o)
             -    \_"'-
`,
    label: 'chill cat',
  },
  {
    art: String.raw`
         |\      _,,,---,,_
   ZZZzz /,.-''    -.  ;-;;,_
        |,4-  ) )-,_. ,\ (  '-'
       '---''(_/--'  '-\_)
`,
    label: 'sleepy cat',
  },
  {
    art: String.raw`
  +---------------+
  |   ~~ LOFI ~~  |
  |               |
  |  beats to     |
  |  code to      |
  |               |
  +---------------+
`,
    label: 'beats to code to',
  },
  {
    art: String.raw`
     .  *  . .  * .  .
   .  .  *  .  . . *
  ---------------------
  /  3:AM      ######  \
 |  coffee      ~~~     |
 |  and code    v0.1.0  |
  \_____________________/
`,
    label: '3am vibes',
  },
  {
    art: String.raw`
    _____
   |     |
   | | | |
   |_____|
   _|___|_
  |  ___  |
  | |   | |  ~~~
  | |___| |
  |_______|
`,
    label: 'radio vibes',
  },
  {
    art: String.raw`
   .  *  .  . *  .  *
     .  *  . .  .   .
   ___________________
  /                   \
 |   (  ) _   _  (  )  |
 |    ||  |\ /|   ||    |
 |    ||  | v |   ||    |
  \___________________/
   ---- === === ----
`,
    label: 'window view',
  },
  {
    frames: SPINNING_DONUT_FRAMES,
    label: 'spinning donut',
    frameMs: 120,
  },
];

export default function LofiWidget({ data }) {
  const [sceneIdx, setSceneIdx] = useState(0);
  const [ticker, setTicker] = useState(0);
  const [frameIdx, setFrameIdx] = useState(0);
  const preWrapRef = useRef(null);
  const [asciiFontPx, setAsciiFontPx] = useState(10);

  // Cycle through scenes every 12 seconds
  useEffect(() => {
    const id = setInterval(() => {
      setSceneIdx(prev => (prev + 1) % LOCAL_SCENES.length);
    }, 12000);
    return () => clearInterval(id);
  }, []);

  // Update when backend pushes new scene
  useEffect(() => {
    if (data?.art) {
      setTicker(t => t + 1);
    }
    if (data?.frames) {
      setTicker(t => t + 1);
    }
  }, [data]);

  const scene = data?.art || data?.frames ? data : LOCAL_SCENES[sceneIdx];
  const sceneFrames = useMemo(() => {
    if (Array.isArray(scene?.frames) && scene.frames.length > 0) {
      return scene.frames.map(normalizeFrame);
    }
    return [normalizeFrame(scene?.art || '')];
  }, [scene]);
  const frameMs = scene?.frameMs || scene?.frame_ms || 120;

  useEffect(() => {
    setFrameIdx(0);
  }, [sceneIdx, ticker]);

  useEffect(() => {
    if (sceneFrames.length <= 1) return;

    const id = setInterval(() => {
      setFrameIdx(prev => (prev + 1) % sceneFrames.length);
    }, frameMs);

    return () => clearInterval(id);
  }, [sceneFrames, frameMs]);

  const activeFrame = sceneFrames[frameIdx] || '';

  useEffect(() => {
    const preWrap = preWrapRef.current;
    if (!preWrap) return;

    const fit = () => {
      const rect = preWrap.getBoundingClientRect();
      const lines = activeFrame
        .split('\n')
        .map(line => line.replace(/\s+$/g, ''))
        .filter(line => line.length > 0);

      const maxChars = Math.max(...lines.map(line => line.length), 1);
      const lineCount = Math.max(lines.length, 1);
      const usableWidth = Math.max(rect.width - 16, 80);
      const usableHeight = Math.max(rect.height - 14, 60);

      const byWidth = usableWidth / (maxChars * 0.56);
      const byHeight = usableHeight / (lineCount * 1.18);
      const nextFont = clamp(Math.floor(Math.min(byWidth, byHeight)), 10, 40);
      setAsciiFontPx(nextFont);
    };

    fit();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(fit);
      observer.observe(preWrap);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', fit);
    return () => window.removeEventListener('resize', fit);
  }, [activeFrame]);

  return (
    <WidgetCard className="lofi-widget" scaleWithCard={false}>
      <div className="flex flex-col items-center justify-center h-full relative w-full">
        {/* Scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.03] bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,0,0,0.3)_2px,rgba(0,0,0,0.3)_4px)]" />

        {/* ASCII art with fade transition */}
        <div ref={preWrapRef} className="flex-1 w-full flex items-center justify-center overflow-hidden px-1">
        <AnimatePresence mode="wait">
          <motion.pre
            key={scene.label + ticker + frameIdx}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="text-glance-accent font-mono leading-[1.2] whitespace-pre select-none text-center"
            style={{
              textShadow: '0 0 8px rgba(56, 189, 248, 0.3)',
              fontSize: `${asciiFontPx}px`,
            }}
          >
            {activeFrame}
          </motion.pre>
        </AnimatePresence>
        </div>

        {/* Label */}
        <motion.div
          key={scene.label + '-label'}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-1 text-[10px] text-glance-muted/70 font-mono tracking-widest uppercase"
        >
          - {scene.label} -
        </motion.div>

        {/* Subtle animated dots */}
        <div className="flex gap-1 mt-1.5 mb-0.5">
          {[0, 1, 2].map(i => (
            <motion.span
              key={i}
              animate={{ opacity: [0.2, 0.8, 0.2] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
              className="w-1 h-1 rounded-full bg-glance-accent/50"
            />
          ))}
        </div>
      </div>
    </WidgetCard>
  );
}

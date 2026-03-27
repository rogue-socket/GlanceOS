import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import WidgetCard from '../WidgetCard';

// Client-side fallback scenes for instant display
const LOCAL_SCENES = [
  {
    art: `
     _._     _,-'""\`-._
    (,-.\`._,'(       |\\'-/|
        \`-.-' \\ )-\`( , o o)
              \`-    \\\`_\`"'-`,
    label: 'chill cat',
  },
  {
    art: `
        |\\      _,,,---,,_
  ZZZzz /,\`.-'\`'    -.  ;-;;,_
       |,4-  ) )-,_. ,\\ (  \`'-'
      '---''(_/--'  \`-'\\_)`,
    label: 'sleepy cat',
  },
  {
    art: `
  ╔═══════════════╗
  ║  ~~  LOFI  ~~ ║
  ║               ║
  ║  ♪ ♫  ♪ ♫  ♪ ║
  ║    beats to   ║
  ║   code to     ║
  ║               ║
  ╚═══════════════╝`,
    label: 'beats to code to',
  },
  {
    art: `
     .  *  . .  * .  .
   .  .  *  .  . . *
  ─────────────────────
  ╭─────────╮
  │  ✧ 3:AM │  ░░▒▒▓▓█
  │  coffee  │  ♪ ~ ♫ ~
  │  & code  │  v0.1.0
  ╰─────────╯`,
    label: '3am vibes',
  },
  {
    art: `
   _____
  |     |
  | | | |
  |_____|
  _|___|_
 |  ___  |
 | |   | |   ♪ ♫ ♪
 | |___| |
 |_______|`,
    label: 'radio vibes',
  },
  {
    art: `
  .  *  .  . *  .  *
    .  *  . .  .   .
  ___________________
 /                   \\
|   (  ) _   _  (  )  |
|    ||  |\\ /|   ||    |
|    ||  | v |   ||    |
 \\___________________/
  ---- === === ----`,
    label: 'window view',
  },
];

export default function LofiWidget({ data }) {
  const [sceneIdx, setSceneIdx] = useState(0);
  const [ticker, setTicker] = useState(0);

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
  }, [data]);

  const scene = data?.art ? data : LOCAL_SCENES[sceneIdx];

  return (
    <WidgetCard className="lofi-widget">
      <div className="flex flex-col items-center justify-center h-full relative">
        {/* Scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.03] bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,0,0,0.3)_2px,rgba(0,0,0,0.3)_4px)]" />

        {/* ASCII art with fade transition */}
        <AnimatePresence mode="wait">
          <motion.pre
            key={scene.label + ticker}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
            className="text-glance-accent font-mono text-[9px] leading-[1.3] whitespace-pre select-none"
            style={{ textShadow: '0 0 8px rgba(56, 189, 248, 0.3)' }}
          >
            {scene.art}
          </motion.pre>
        </AnimatePresence>

        {/* Label */}
        <motion.div
          key={scene.label + '-label'}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-2 text-[10px] text-glance-muted/70 font-mono tracking-widest uppercase"
        >
          ─ {scene.label} ─
        </motion.div>

        {/* Subtle animated dots */}
        <div className="flex gap-1 mt-2">
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

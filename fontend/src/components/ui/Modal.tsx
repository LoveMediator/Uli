import type { PropsWithChildren } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

type ModalProps = PropsWithChildren<{
  open: boolean;
  onClose: () => void;
}>;

export function Modal({ open, onClose, children }: ModalProps) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-40 flex items-end bg-coffee-900/30 px-4 pb-6 backdrop-blur-[2px]"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: 40 }}
            animate={{ y: 0 }}
            exit={{ y: 20 }}
            transition={{ duration: 0.2 }}
            className="w-full"
            onClick={(event) => event.stopPropagation()}
          >
            {children}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

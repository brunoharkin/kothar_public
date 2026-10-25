import React, { useState, useEffect, useRef } from "react";
import {
    Command,
    Paperclip,
    ArrowUp,
    CornerDownLeft,
    Loader2
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

const SYSTEM_PROMPTS = [
    "Iniciar orquestração Kothar v3.0...",
    "Compilar lógica do modelo selecionado...",
    "Analisar histórico de trace da sessão...",
    "Executar prompt paralelo nas colunas...",
];

interface AIChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  disabled: boolean;
  modelName: string;
}

export const AIChatInput = ({ value, onChange, onSubmit, isLoading, disabled }: AIChatInputProps) => {
    const [promptIndex, setPromptIndex] = useState(0);
    const [isExpanded, setIsExpanded] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (isExpanded || value) return;
        const interval = setInterval(() => {
            setPromptIndex((prev) => (prev + 1) % SYSTEM_PROMPTS.length);
        }, 4000);
        return () => clearInterval(interval);
    }, [isExpanded, value]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                if (!value) setIsExpanded(false);
            }
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isExpanded) {
                setIsExpanded(false);
                inputRef.current?.blur();
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        window.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [value, isExpanded]);

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
        }
    }, [value]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!value.trim() || disabled) return;
        onSubmit();
        // Garante que o input mantenha o foco após limpar o valor
        setTimeout(() => inputRef.current?.focus(), 10);
    };

    return (
        <div className="ai-chat-input-wrapper">
            <motion.div
                ref={containerRef}
                layout
                transition={{ type: "spring", stiffness: 380, damping: 32, mass: 0.8 }}
                className={`ai-chat-input-container ${isExpanded ? "expanded" : "collapsed"}`}
                onClick={() => {
                    setIsExpanded(true);
                    inputRef.current?.focus();
                }}
            >
                <div className="ai-chat-input-inner">
                    <div className="ai-chat-top-bar">
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="ai-chat-btn-command"
                        >
                            <Command size={15} />
                        </motion.div>

                        <form onSubmit={handleSubmit} className="ai-chat-form">
                            <textarea
                                ref={inputRef}
                                value={value}
                                onChange={(e) => onChange(e.target.value)}
                                onFocus={() => setIsExpanded(true)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit();
                                  }
                                }}
                                rows={1}
                                className="ai-chat-textarea"
                                style={{ minHeight: '32px', maxHeight: '200px', overflowY: 'auto' }}
                            />

                            {!value && (
                                <div className="ai-chat-placeholder-wrapper">
                                    <AnimatePresence mode="wait">
                                        <motion.span
                                            key={promptIndex}
                                            initial={{ opacity: 0, y: 6, filter: "blur(2px)" }}
                                            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                            exit={{ opacity: 0, y: -6, filter: "blur(2px)" }}
                                            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                                            className="ai-chat-placeholder"
                                        >
                                            {disabled ? "Offline ou Processando..." : SYSTEM_PROMPTS[promptIndex]}
                                        </motion.span>
                                    </AnimatePresence>
                                </div>
                            )}
                        </form>

                        <div className="ai-chat-actions">
                            <motion.button
                                type="button"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="ai-chat-btn-attach"
                                title="Anexar Arquivo"
                            >
                                <Paperclip size={15} />
                            </motion.button>

                            <motion.button
                                type="button"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleSubmit();
                                }}
                                disabled={disabled || !value.trim()}
                                whileHover={value.trim() && !disabled ? { scale: 1.05 } : {}}
                                whileTap={value.trim() && !disabled ? { scale: 0.95 } : {}}
                                className={`ai-chat-btn-submit ${value.trim() && !disabled ? "active" : "disabled"}`}
                            >
                                {isLoading ? <Loader2 size={15} className="animate-spin" /> : value.trim() ? <ArrowUp size={15} /> : <CornerDownLeft size={13} />}
                            </motion.button>
                        </div>
                    </div>

                    <AnimatePresence>
                        {isExpanded && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{
                                    opacity: { duration: 0.2 },
                                    height: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
                                }}
                                className="ai-chat-expanded-tray"
                            >
                                <div className="ai-chat-tray-inner">
                                    <div className="ai-chat-tray-tools" style={{ width: '100%', justifyContent: 'space-between' }}>
                                        <motion.button
                                            type="button"
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            className="ai-chat-btn-attach mobile-only"
                                            title="Anexar Arquivo"
                                        >
                                            <Paperclip size={15} />
                                        </motion.button>


                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    );
};

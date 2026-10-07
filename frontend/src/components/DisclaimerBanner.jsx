import React from 'react';
import { AlertTriangle } from 'lucide-react';

const DisclaimerBanner = () => {
  return (
    <div className="bg-amber-500 text-white text-xs sm:text-sm px-4 py-2 text-center flex items-center justify-center gap-2 font-medium shadow-inner">
      <AlertTriangle className="w-4 h-4 shrink-0" />
      <span>
        <strong>Medical Disclaimer:</strong> MediAssist AI is an educational decision-support platform — <strong>not a diagnostic system</strong>. It does not replace professional medical advice. In an emergency, call 78160/40549 immediately.
      </span>
    </div>
  );
};

export default DisclaimerBanner;

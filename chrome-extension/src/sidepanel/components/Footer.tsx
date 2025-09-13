interface FooterProps {
  onCancel: () => void;
}

export const Footer = ({ onCancel }: FooterProps) => (
  <div className="p-4 bg-black">
    <button
      onClick={onCancel}
      className="w-full px-6 py-3 bg-transparent border-2 border-custom-gold text-custom-gold font-bold rounded-lg uppercase tracking-widest transition-all duration-300 hover:bg-custom-gold hover:text-black"
    >
      Cancel
    </button>
  </div>
);

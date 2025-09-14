export interface Claim {
  timestamp: string;
  text: string;
  type: 'Opinion' | 'Fact';
  score: number;
  synthesis: string;
  isVerified?: boolean;
  startSeconds?: number;
  verdict?: string;
  sources?: string[];
}

export interface Speaker {
    name: string;
    party: string;
    truthRate: string;
}

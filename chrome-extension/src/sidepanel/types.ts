export interface Claim {
  timestamp: string;
  text: string;
  type: 'Opinion' | 'Fact';
  score: number;
  synthesis: string;
}

export interface Speaker {
    name: string;
    party: string;
    truthRate: string;
}

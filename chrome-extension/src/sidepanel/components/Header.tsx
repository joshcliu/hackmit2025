import { Bell, UserCircle } from 'lucide-react';

export const Header = () => (
  <div className="flex items-center justify-between p-4 border-b border-gray-200">
    <div className="flex items-center">
      <input type="checkbox" id="show-speaker" className="mr-2" />
      <label htmlFor="show-speaker" className="text-sm">Show only Speaker X</label>
    </div>
    <div className="flex items-center space-x-4">
      <Bell className="h-6 w-6 text-gray-500" />
      <UserCircle className="h-8 w-8 text-gray-500" />
    </div>
  </div>
);

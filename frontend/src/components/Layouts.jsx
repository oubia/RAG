import { Outlet, useNavigate } from 'react-router-dom';

const Layout = () => {


  return (
  
    <div className='flex flex-col sticky'>


  <div className='flex-grow sticky'>
  <Outlet />
  </div>
</div>

  );
};

export default Layout;
